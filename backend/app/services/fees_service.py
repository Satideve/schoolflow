# backend/app/services/fees_service.py
"""
High-level fee operations: invoice generation, payment handling, receipts.
"""
from decimal import Decimal
from datetime import datetime
from app.repositories.fee_repo import create_invoice, create_payment, mark_invoice_paid, create_receipt
from app.services.payments.interface import PaymentGatewayInterface
from app.services.pdf.renderer import render_receipt_pdf
from app.services.messaging.interface import MessagingInterface
from sqlalchemy.orm import Session
import os
from pathlib import Path
import uuid

RECEIPTS_DIR = Path("data/receipts")
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

class FeesService:
    def __init__(self, db: Session, payment_gateway: PaymentGatewayInterface, messaging: MessagingInterface):
        self.db = db
        self.gateway = payment_gateway
        self.messaging = messaging

    def generate_invoice_for_student(self, student_id: int, period: str, amount: Decimal, due_date: datetime):
        """Create a fee invoice and return it."""
        invoice = create_invoice(self.db, student_id=student_id, period=period, amount_due=amount, due_date=due_date)
        return invoice

    def create_payment_order(self, invoice_id: int, amount: Decimal):
        """Create a payment order via the payment gateway adapter."""
        # convert to rupees float
        order = self.gateway.create_order(float(amount), currency="INR", receipt=str(invoice_id))
        return order

    def handle_webhook_mark_paid(self, webhook_payload: bytes, signature: str) -> dict:
        """Verify webhook and create Payment + Receipt + mark invoice paid."""
        # Verify signature
        ok = self.gateway.verify_webhook(webhook_payload, signature)
        if not ok:
            raise ValueError("Webhook verification failed")

        # For FakeAdapter we expect JSON with provider_txn_id, invoice_id, amount, idempotency_key
        import json
        data = json.loads(webhook_payload.decode("utf-8"))
        provider_txn_id = data.get("provider_txn_id")
        invoice_id = int(data.get("invoice_id"))
        amount = Decimal(str(data.get("amount")))
        idempotency_key = data.get("idempotency_key")

        # Check idempotency: query payment with idempotency_key
        existing = self.db.query(__import__("app.models.fee.payment", fromlist=["Payment"]).Payment).filter_by(idempotency_key=idempotency_key).first()
        if existing:
            return {"status": "ignored", "reason": "idempotent replay"}

        payment = create_payment(self.db, fee_invoice_id=invoice_id, provider="fake", provider_txn_id=provider_txn_id, amount=amount, status="captured", idempotency_key=idempotency_key)
        # mark invoice paid
        invoice = self.db.query(__import__("app.models.fee.fee_invoice", fromlist=["FeeInvoice"]).FeeInvoice).get(invoice_id)
        mark_invoice_paid(self.db, invoice)

        # create receipt
        receipt_no = f"REC-{uuid.uuid4().hex[:10].upper()}"
        pdf_path = str(RECEIPTS_DIR / f"{receipt_no}.pdf")
        # Render PDF
        student = {"name": "Student #" + str(invoice.student_id)}  # stub; ideally fetch student
        ctx = {"invoice": {"id": invoice.id, "amount": float(invoice.amount_due), "period": invoice.period}, "student": student, "payment": {"provider_txn_id": provider_txn_id, "amount": float(amount), "receipt_no": receipt_no}}
        render_receipt_pdf(ctx, pdf_path)
        receipt = create_receipt(self.db, payment_id=payment.id, receipt_no=receipt_no, pdf_path=pdf_path)
        # send email via messaging adapter (fake or SMTP)
        self.messaging.send_email(to_email="parent@example.com", subject=f"Receipt #{receipt_no}", body_html=f"<p>Receipt generated. Download: {pdf_path}</p>")
        return {"status": "ok", "receipt": receipt_no, "pdf_path": pdf_path}
