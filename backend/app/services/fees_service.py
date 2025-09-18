# backend/app/services/fees_service.py
"""
High-level fee operations: invoice generation, payment handling, receipts.
"""
from decimal import Decimal
from datetime import datetime
from pathlib import Path
import uuid
import os
import json

from sqlalchemy.orm import Session

from app.repositories.fee_repo import (
    create_invoice,
    create_payment,
    mark_invoice_paid,
    create_receipt,
)
from app.services.payments.interface import PaymentGatewayInterface
from app.services.pdf.renderer import render_receipt_pdf
from app.services.messaging.interface import MessagingInterface
from app.models.fee.fee_invoice import FeeInvoice

RECEIPTS_DIR = Path("data/receipts")
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

class FeesService:
    def __init__(
        self,
        db: Session,
        payment_gateway: PaymentGatewayInterface,
        messaging: MessagingInterface,
    ):
        self.db = db
        self.gateway = payment_gateway
        self.messaging = messaging

    def generate_invoice_for_student(
        self, student_id: int, period: str, amount: Decimal, due_date: datetime
    ):
        """Create a fee invoice and return it."""
        invoice = create_invoice(
            self.db,
            student_id=student_id,
            period=period,
            amount_due=amount,
            due_date=due_date,
        )
        return invoice

    def create_payment_order(self, invoice_id: int, amount: Decimal):
        """Create a payment order via the payment gateway adapter."""
        order = self.gateway.create_order(
            float(amount), currency="INR", receipt=str(invoice_id)
        )
        return order

    
    # def handle_webhook_mark_paid(self, webhook_payload: bytes, signature: str) -> dict:
    def handle_webhook_mark_paid(self, webhook_payload: bytes, signature: str, pdf_options: dict | None = None) -> dict:

        """Verify webhook and create Payment + Receipt + mark invoice paid."""
        # 1) signature check
        if not self.gateway.verify_webhook(webhook_payload, signature):
            raise ValueError("Webhook verification failed")

        # 2) parse JSON
        data = json.loads(webhook_payload.decode("utf-8"))

        # 3) invoice lookup
        raw_id = data.get("invoice_id")
        if raw_id is None:
            raise ValueError("Missing invoice_id in webhook payload")
        invoice_id = int(raw_id)

        invoice: FeeInvoice = self.db.query(FeeInvoice).get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        # 4) derive other fields, with sensible defaults
        provider_txn_id = data.get("provider_txn_id") or f"auto-{uuid.uuid4().hex}"
        amount_field = data.get("amount")
        if amount_field is not None:
            amount = Decimal(str(amount_field))
        else:
            amount = invoice.amount_due

        idempotency_key = data.get("idempotency_key") or provider_txn_id

        # 5) idempotency guard
        existing = (
            self.db.query(__import__("app.models.fee.payment", fromlist=["Payment"]).Payment)
            .filter_by(idempotency_key=idempotency_key)
            .first()
        )
        if existing:
            return {"status": "ignored", "reason": "idempotent replay"}

        # 6) record payment
        payment = create_payment(
            self.db,
            fee_invoice_id=invoice_id,
            provider="fake",
            provider_txn_id=provider_txn_id,
            amount=amount,
            status="captured",
            idempotency_key=idempotency_key,
        )

        # 7) mark invoice paid
        mark_invoice_paid(self.db, invoice)

        # 8) generate receipt PDF
        receipt_no = f"REC-{uuid.uuid4().hex[:10].upper()}"
        pdf_path = str(RECEIPTS_DIR / f"{receipt_no}.pdf")

        ctx = {
            "invoice": {
                "id": invoice.id,
                "amount": float(invoice.amount_due),
                "period": invoice.period,
            },
            "student": {"name": f"Student #{invoice.student_id}"},
            "payment": {
                "provider_txn_id": provider_txn_id,
                "amount": float(amount),
                "receipt_no": receipt_no,
            },
        }
        render_receipt_pdf(ctx, pdf_path)

        # 9) persist receipt record
        receipt = create_receipt(
            self.db,
            payment_id=payment.id,
            receipt_no=receipt_no,
            pdf_path=pdf_path,
        )

        # 10) send notification
        self.messaging.send_email(
            to_email="parent@example.com",
            subject=f"Receipt #{receipt_no}",
            body_html=f"<p>Your fee receipt is ready: {pdf_path}</p>",
        )

        return {"status": "ok", "receipt": receipt_no, "pdf_path": pdf_path}
