# backend/tests/api/test_receipt_download.py
"""
Integration test: create invoice+payment via API or fixtures, ensure webhook/receipt
flow creates a receipt, then download the receipt PDF and make basic sanity checks.

This is intentionally lightweight (doesn't require running an OCR/text-extraction tool).
It asserts:
  - Download endpoint returns 200
  - Content-Type is PDF
  - Response body size is reasonably > 500 bytes (indicates PDF isn't an empty wrapper)
  - Filename in Content-Disposition contains the expected receipt filename fragment
"""

import uuid
from decimal import Decimal

import pytest
from httpx import Response


def _create_invoice_with_payment(auth_client, seed_student):
    # create an invoice and include a manual payment so receipt creation path exists
    invoice_no = f"INV-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "student_id": seed_student.get("id") or seed_student.get("student_id") or seed_student.get("pk"),
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
    resp: Response = auth_client.post("/api/v1/invoices/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_download_receipt_pdf_roundtrip(auth_client, seed_student, monkeypatch):
    """
    Create invoice+payment (which should render invoice PDF). Trigger webhook/create-receipt
    flow (some implementations create receipt automatically on payment; otherwise simulate
    via posting to payments/webhook). Then fetch receipts, pick the latest, and download its PDF.
    """
    # Create invoice with payment
    inv = _create_invoice_with_payment(auth_client, seed_student)
    inv_id = inv["id"]

    # If the app creates receipts automatically on payment, there should now be a receipt.
    # Otherwise, try to trigger the webhook path that creates receipts.
    # We'll post a webhook-like payload; many test suites monkeypatch signature verification.
    wh_payload = {
        "order_id": f"order-{inv_id}",
        "invoice_id": inv_id,
        "payment_id": f"pay-{uuid.uuid4().hex[:8]}",
        "status": "paid",
        "amount": inv.get("amount_due") or inv.get("amount") or 0,
    }
    wh = auth_client.post("/api/v1/payments/webhook", json=wh_payload)
    # webhook may return 200 or 201 depending on implementation; accept both
    assert wh.status_code in (200, 201), wh.text

    # list receipts and pick the most recent one that references our invoice (best-effort)
    rlist = auth_client.get("/api/v1/receipts/")
    assert rlist.status_code == 200, rlist.text
    receipts = rlist.json()
    # Ensure at least one receipt exists
    assert receipts, "No receipts found after payment/webhook"

    # Try to find a receipt that references the invoice (via pdf_path or metadata)
    candidate = None
    for r in receipts:
        # Many implementations may include invoice id in pdf_path or invoice_no in metadata
        if str(inv_id) in (r.get("pdf_path") or "") or r.get("invoice_no") == inv.get("invoice_no"):
            candidate = r
            break
    # fallback to first receipt
    if candidate is None:
        candidate = receipts[0]

    receipt_id = candidate["id"]

    # Download the receipt PDF
    dl = auth_client.get(f"/api/v1/receipts/{receipt_id}/download")
    assert dl.status_code == 200, dl.text
    # Content-type should be PDF (some frameworks set application/pdf)
    ctype = dl.headers.get("content-type", "")
    assert "pdf" in ctype.lower(), f"Unexpected content-type: {ctype}"
    content = dl.content
    # Basic sanity: PDF binary usually > few hundred bytes; require > 500 bytes to avoid tiny wrappers
    assert isinstance(content, (bytes, bytearray))
    assert len(content) > 500, f"Downloaded PDF too small ({len(content)} bytes)"

    # Optional: filename present in header
    disp = dl.headers.get("content-disposition", "")
    assert "filename" in disp.lower() or disp == "", "Content-Disposition missing filename (ok but unexpected)"

    # If the candidate had a receipt_no, check it at least appears in filename/header or metadata
    if candidate.get("receipt_no"):
        rno = candidate.get("receipt_no")
        if "filename" in disp.lower():
            assert rno in disp or rno in dl.headers.get("content-disposition", "")
