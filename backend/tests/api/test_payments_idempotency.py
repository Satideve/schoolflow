# backend/tests/api/test_payments_idempotency.py
import uuid
import pytest
from httpx import Response
from sqlalchemy.orm import Session

# Reuses existing fixtures: auth_client, seed_invoice, db_session

def test_webhook_is_idempotent(auth_client, seed_invoice, db_session: Session):
    """
    Send the same webhook (same idempotency_key) twice:
      - First call -> 200 ok (creates 1 payment + 1 receipt)
      - Second call -> 200 ignored (no new payment/receipt)
      - Final assertion: exactly one payment remains for the invoice
    """
    invoice = seed_invoice
    invoice_id = invoice["id"]

    # Stable idempotency key we will reuse
    idem = f"idemp-{invoice_id}-test-{uuid.uuid4().hex[:6]}"

    payload = {
        "order_id": f"order-{invoice_id}",
        "invoice_id": invoice_id,
        "payment_id": f"pay-{uuid.uuid4().hex[:8]}",
        "status": "paid",
        "amount": invoice.get("amount_due") or invoice.get("amount") or 0,
        "idempotency_key": idem,
        # set a provider_txn_id so receipts are consistent
        "provider_txn_id": f"auto-{uuid.uuid4().hex}",
    }

    # 1) First webhook -> should create payment/receipt
    r1: Response = auth_client.post("/api/v1/payments/webhook", json=payload)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert body1.get("status") in ("ok", "created")

    # 2) Second webhook with same idempotency_key -> ignored
    r2: Response = auth_client.post("/api/v1/payments/webhook", json=payload)
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2.get("status") == "ignored"
    assert body2.get("reason") == "idempotent replay"

    # 3) DB: verify only ONE payment exists for this invoice
    from app.models.fee.payment import Payment
    payments = (
        db_session.query(Payment)
        .filter(Payment.fee_invoice_id == invoice_id)
        .all()
    )
    # Only one payment should exist for this invoice (the first call)
    assert len(payments) == 1, f"Expected 1 payment, found {len(payments)}"
