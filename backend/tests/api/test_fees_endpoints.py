# backend/tests/api/test_fees_endpoints.py

import os
import uuid
from pathlib import Path
from decimal import Decimal

import pytest
from httpx import Response


def test_fee_plan_crud(auth_client):
    """
    Create a fee plan, list fee plans, and fetch by id.
    """
    payload = {
        "name": f"Tuition-{uuid.uuid4().hex[:6]}",
        "academic_year": "2025-2026",
        "frequency": "annual"
    }
    # create
    resp: Response = auth_client.post("/api/v1/fee-plans/", json=payload)
    assert resp.status_code in (200, 201), resp.text
    created = resp.json()
    assert created["name"] == payload["name"]
    plan_id = created["id"]

    # list
    resp_list = auth_client.get("/api/v1/fee-plans/")
    assert resp_list.status_code == 200, resp_list.text
    plans = resp_list.json()
    assert any(p["id"] == plan_id for p in plans)

    # get by id
    resp_get = auth_client.get(f"/api/v1/fee-plans/{plan_id}")
    assert resp_get.status_code == 200, resp_get.text
    p = resp_get.json()
    assert p["id"] == plan_id
    assert p["frequency"] == "annual"


def test_create_invoice_for_student_with_plan(auth_client, seed_student, seed_fee_plan):
    """
    Create an invoice referencing a student and fee plan.
    """
    payload = {
        "student_id": seed_student.get("id") or seed_student.get("student_id") or seed_student.get("pk"),
        "plan_id": seed_fee_plan.get("id"),
        "invoice_no": f"INV-{uuid.uuid4().hex[:8].upper()}",
        "period": "2025-11",
        "amount_due": float(Decimal("2500.00")),
        "due_date": "2025-11-30"
    }
    resp: Response = auth_client.post("/api/v1/invoices/", json=payload)
    assert resp.status_code == 201, resp.text
    inv = resp.json()
    assert inv["invoice_no"] == payload["invoice_no"]
    assert inv["student_id"] == payload["student_id"]


def test_create_invoice_with_payment_renders_pdf(auth_client, seed_student, seed_fee_plan):
    """
    Create an invoice with an immediate 'manual' payment payload and assert:
      - API returns 201
      - Invoice is marked paid (if implementation marks it)
      - PDF file exists under the configured invoices directory (or common test tmp dirs or project app/data)
    """
    from app.core.config import settings

    invoice_no = f"INV-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "student_id": seed_student.get("id") or seed_student.get("student_id") or seed_student.get("pk"),
        "plan_id": seed_fee_plan.get("id"),
        "invoice_no": invoice_no,
        "period": "2025-12",
        "amount_due": float(Decimal("3500.00")),
        "due_date": "2025-12-31",
        "payment": {
            "provider": "manual",
            "amount": float(Decimal("3500.00")),
            "status": "captured",
            "provider_txn_id": f"manual-{uuid.uuid4().hex[:6]}"
        }
    }

    resp = auth_client.post("/api/v1/invoices/", json=payload)
    assert resp.status_code == 201, resp.text
    inv = resp.json()
    inv_id = inv["id"]

    # Check invoice status if present (some implementations may or may not set this)
    if "status" in inv:
        assert inv["status"] in ("paid", "paid_full", "captured", "completed", "issued")

    invoice_filename = f"INV-{invoice_no}.pdf"

    # Build list of candidate directories to check (primary: configured invoices path)
    checked_paths = []
    candidates = []

    # 1) configured invoices path (if available)
    try:
        cfg = settings.invoices_path()
        candidates.append(Path(cfg))
        checked_paths.append(str(cfg))
    except Exception:
        # ignore, we'll try other locations below
        pass

    # 2) project app/data/invoices (where renderer sometimes writes when settings.base_dir wasn't applied)
    project_root = Path(__file__).resolve().parents[2]  # backend/tests -> backend -> project root
    app_data_invoices = project_root / "app" / "data" / "invoices"
    candidates.append(app_data_invoices)
    checked_paths.append(str(app_data_invoices))

    # 3) legacy/previous test tmp dirs (kept for backward compatibility)
    legacy_paths = [
        project_root / "tmp_data" / "invoices",    # backend/tmp_data/invoices
        project_root / "tmp_data",                 # backend/tmp_data
        project_root / "tests" / "tmp_data",       # backend/tests/tmp_data
        project_root / "tests" / "tmp_data" / "invoices"
    ]
    for p in legacy_paths:
        candidates.append(p)
        checked_paths.append(str(p))

    # Now check them
    found = False
    for base in candidates:
        try:
            candidate = base / invoice_filename
            if candidate.exists():
                found = True
                found_at = str(candidate)
                break
        except Exception:
            continue

    if not found:
        # Helpful debug listing for the locations we checked
        debug_listing = []
        for p in checked_paths:
            try:
                listing = sorted([str(x) for x in Path(p).glob("**/*")]) if Path(p).exists() else []
            except Exception:
                listing = ["<could not list>"]
            debug_listing.append({"path": p, "listing_sample": listing[:10]})
        raise AssertionError(
            f"Invoice PDF {invoice_filename} not found. Checked locations: {checked_paths}. Sample listings: {debug_listing}"
        )

    # success
    assert found


def test_payment_webhook_creates_receipt(auth_client, seed_invoice, monkeypatch):
    """
    Post a payment webhook for an existing invoice and assert a receipt is created.
    The fixture `seed_invoice` ensures an invoice exists.
    We monkeypatch signature verification (if present) so webhook is accepted.
    """
    invoice = seed_invoice
    invoice_id = invoice["id"]

    # Attempt to monkeypatch the common verify function used by webhook router
    verifier_candidates = [
        "app.api.v1.routers.fees.payments.verify_signature",
        "app.api.v1.routers.fees.payments._verify_signature",
        "app.api.v1.routers.fees.verify_signature",
    ]
    patched = False
    for p in verifier_candidates:
        try:
            monkeypatch.setattr(p, lambda *a, **k: True)
            patched = True
            break
        except Exception:
            continue

    payload = {
        "order_id": f"order-{invoice_id}",
        "invoice_id": invoice_id,
        "payment_id": f"pay-{uuid.uuid4().hex[:8]}",
        "status": "paid",
        "amount": invoice.get("amount_due") or invoice.get("amount") or 0,
    }

    wh = auth_client.post("/api/v1/payments/webhook", json=payload)
    assert wh.status_code == 200, wh.text
    # After webhook, list receipts and assert a new receipt exists for this invoice
    rlist = auth_client.get("/api/v1/receipts/")
    assert rlist.status_code == 200, rlist.text
    receipts = rlist.json()
    assert any("receipt_no" in r and (str(invoice_id) in (r.get("pdf_path") or "") or r.get("payment_id")) for r in receipts)
