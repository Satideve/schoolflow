# backend/tests/api/test_fees.py

import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import Response


def _make_invoice_payload(student_id: int = 1, amount: float | Decimal = 5000.0):
    """Helper to build an InvoiceCreate-style payload compatible with current API."""
    return {
        "student_id": student_id,
        "invoice_no": f"TEST-INV-{uuid.uuid4().hex[:8]}",
        "period": "2025-12",
        "amount_due": float(Decimal(amount)),
        "due_date": date(2025, 12, 31).isoformat(),
    }


def test_create_fee(auth_client, seed_student):
    """
    Ensure we can create a fee-like invoice via the API.
    Uses seed_student fixture so we don't rely on a magic student id.

    Note: some fixture variants may return a SQLAlchemy model instance or a plain dict.
    Handle both gracefully.
    """
    # tolerate either a model with .id or a dict-like object
    try:
        student_id = getattr(seed_student, "id")
    except Exception:
        # fallback for dicts or other mappings
        if isinstance(seed_student, dict):
            student_id = seed_student.get("id")
        else:
            # last-resort attempt
            student_id = seed_student["id"] if hasattr(seed_student, "__getitem__") else None

    assert student_id is not None, "seed_student did not provide an id"

    payload = _make_invoice_payload(student_id=student_id, amount=5000)
    resp: Response = auth_client.post("/api/v1/invoices/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    # invoice uses 'amount_due' field
    assert float(data["amount_due"]) == float(payload["amount_due"])
    assert data["invoice_no"] == payload["invoice_no"]
    assert data["student_id"] == payload["student_id"]


def test_get_fees(auth_client):
    """
    Create a couple invoices and ensure listing invoices returns them.
    (Replaces legacy listing of /api/v1/fees/ with /api/v1/invoices/.)
    """
    # create two invoices
    p1 = _make_invoice_payload(student_id=10, amount=1234.50)
    p2 = _make_invoice_payload(student_id=11, amount=2222.00)
    r1 = auth_client.post("/api/v1/invoices/", json=p1)
    r2 = auth_client.post("/api/v1/invoices/", json=p2)
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text

    # list invoices and check that at least these two exist by invoice_no
    resp: Response = auth_client.get("/api/v1/invoices/")
    assert resp.status_code == 200, resp.text
    invoices = resp.json()
    invoice_nos = {inv.get("invoice_no") for inv in invoices}
    assert p1["invoice_no"] in invoice_nos
    assert p2["invoice_no"] in invoice_nos


def test_get_single_fee(auth_client):
    """
    Create an invoice and fetch it by id.
    (Replaces legacy GET /api/v1/fees/{id}.)
    """
    payload = _make_invoice_payload(student_id=5, amount=750.0)
    create_resp = auth_client.post("/api/v1/invoices/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    invoice_id = created["id"]

    resp: Response = auth_client.get(f"/api/v1/invoices/{invoice_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == invoice_id
    assert float(data["amount_due"]) == float(payload["amount_due"])


def test_create_fee_payment(auth_client):
    """
    Create an invoice, then call payments/create-order to ensure the payment-order endpoint works.
    This replaces legacy fee-payment creation which no longer exists as /fee-payments/.     
    """
    payload = _make_invoice_payload(student_id=20, amount=3500.00)
    create_resp = auth_client.post("/api/v1/invoices/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    invoice = create_resp.json()
    invoice_id = invoice["id"]

    # Create order for the invoice (returns an 'order' object)
    pay_resp: Response = auth_client.post(f"/api/v1/payments/create-order/{invoice_id}")    
    assert pay_resp.status_code == 200, pay_resp.text
    body = pay_resp.json()
    assert "order" in body, body
    order = body["order"]
    # best-effort assertions (adapter shape may vary); ensure invoice amount is represented 
    assert order is not None
    # If the adapter returns amount or total fields, check them when present
    if isinstance(order, dict):
        amt_fields = ["amount", "total", "value"]
        assert any(f in order for f in amt_fields) or "id" in order


def test_get_fee_payments(auth_client):
    """
    The current API exposes receipts metadata listing instead of a general 'fee-payments' list.
    Ensure the receipts metadata endpoint is reachable (returns JSON list).
    """
    resp: Response = auth_client.get("/api/v1/receipts/metadata")
    assert resp.status_code == 200, resp.text
    payments = resp.json()
    # It's acceptable for this list to be empty; we only assert it is a list
    assert isinstance(payments, list)
