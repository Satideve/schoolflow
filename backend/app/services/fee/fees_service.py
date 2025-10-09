# backend/app/services/fee/fees_service.py
"""
High-level fee operations: invoice generation, payment handling, receipts.
"""
from decimal import Decimal
from datetime import datetime
from pathlib import Path
import uuid
import json

from sqlalchemy.orm import Session

from app.repositories.invoice_repo import get_invoice_by_no, create_invoice
from app.repositories.fee_repo import create_payment, mark_invoice_paid, create_receipt
from app.services.payments.interface import PaymentGatewayInterface
from app.services.pdf.renderer import render_receipt_pdf, render_invoice_pdf
from app.services.pdf.context_loader import load_receipt_context, load_invoice_context
from app.services.messaging.interface import MessagingInterface
from app.models.fee.fee_invoice import FeeInvoice
from app.core.config import settings


def _ensure_dir(path: Path) -> Path:
    """Ensure the directory exists and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_receipts_dir() -> Path:
    """Return current receipts directory (resolved from settings) and ensure it exists."""
    p = settings.receipts_path()
    return _ensure_dir(Path(p))


def get_invoices_dir() -> Path:
    """Return current invoices directory (resolved from settings) and ensure it exists."""
    p = settings.invoices_path()
    return _ensure_dir(Path(p))


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
        self,
        student_id: int,
        invoice_no: str,
        period: str,
        amount: Decimal,
        due_date: datetime,
        payment: dict | None = None,
    ) -> FeeInvoice:
        """
        Idempotently generate a FeeInvoice record and render its PDF.
        If an invoice with the same invoice_no exists, returns it and
        regenerates PDF only if missing.
        """
        existing = get_invoice_by_no(self.db, invoice_no)
        invoices_dir = get_invoices_dir()

        if existing:
            filename = f"INV-{invoice_no}.pdf"
            pdf_path = invoices_dir / filename
            if not pdf_path.exists():
                ctx = load_invoice_context(existing.id, self.db)
                render_invoice_pdf(ctx, pdf_path)
            return existing

        # Create invoice and commit
        inv = create_invoice(
            self.db,
            student_id=student_id,
            invoice_no=invoice_no,
            period=period,
            amount_due=amount,
            due_date=due_date,
        )
        self.db.commit()
        self.db.refresh(inv)

        # Optional payment handling
        if payment:
            provider_txn_id = payment.get("provider_txn_id") or f"manual-{uuid.uuid4().hex}"
            amt = payment.get("amount")
            try:
                paid_amount = Decimal(str(amt)) if amt is not None else inv.amount_due
            except Exception:
                paid_amount = Decimal(str(float(amt)))

            idempotency_key = payment.get("idempotency_key") or provider_txn_id

            recorded_payment = create_payment(
                self.db,
                fee_invoice_id=inv.id,
                provider=payment.get("provider", "manual"),
                provider_txn_id=provider_txn_id,
                amount=paid_amount,
                status=payment.get("status", "captured"),
                idempotency_key=idempotency_key,
            )

            amount_due_decimal = Decimal(str(inv.amount_due))
            if recorded_payment and recorded_payment.amount >= amount_due_decimal:
                mark_invoice_paid(self.db, inv)

            self.db.commit()
            self.db.refresh(inv)

        # Render PDF after any payment
        filename = f"INV-{invoice_no}.pdf"
        pdf_path = invoices_dir / filename
        ctx = load_invoice_context(inv.id, self.db)
        render_invoice_pdf(ctx, pdf_path)

        return inv

    # ... rest of the class unchanged ...

    def create_payment_order(self, invoice_id: int, amount: Decimal):
        """Create a payment order via the payment gateway adapter."""
        return self.gateway.create_order(
            float(amount), currency="INR", receipt=str(invoice_id)
        )

    def handle_webhook_mark_paid(
        self, webhook_payload: bytes, signature: str, pdf_options: dict | None = None
    ) -> dict:
        """Verify webhook, record payment, mark invoice paid, generate receipt + PDF."""
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
        paid_amount = Decimal(str(amount_field)) if amount_field is not None else invoice.amount_due
        idempotency_key = data.get("idempotency_key") or provider_txn_id

        # 5) idempotency guard
        existing_payment = (
            self.db.query(
                __import__("app.models.fee.payment", fromlist=["Payment"]).Payment
            )
            .filter_by(idempotency_key=idempotency_key)
            .first()
        )
        if existing_payment:
            return {"status": "ignored", "reason": "idempotent replay"}

        # 6) record payment
        payment = create_payment(
            self.db,
            fee_invoice_id=invoice_id,
            provider="fake",
            provider_txn_id=provider_txn_id,
            amount=paid_amount,
            status="captured",
            idempotency_key=idempotency_key,
        )

        # 7) mark invoice paid
        mark_invoice_paid(self.db, invoice)

        # 8) create receipt record
        receipt_no = f"REC-{uuid.uuid4().hex[:10].upper()}"
        receipts_dir = get_receipts_dir()
        pdf_path = receipts_dir / f"{receipt_no}.pdf"
        receipt = create_receipt(
            self.db,
            payment_id=payment.id,
            receipt_no=receipt_no,
            pdf_path=str(pdf_path),
        )

        # 9) render receipt PDF
        ctx = load_receipt_context(receipt.id, self.db)
        render_receipt_pdf(ctx, str(pdf_path))

        # 10) send notification
        self.messaging.send_email(
            to_email="parent@example.com",
            subject=f"Receipt #{receipt_no}",
            body_html=f"<p>Your fee receipt is ready: {pdf_path}</p>",
        )

        return {"status": "ok", "receipt": receipt_no, "pdf_path": str(pdf_path)}
