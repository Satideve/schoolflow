# backend/app/services/fee/receipt_service.py
"""
Receipt creation and PDF rendering service.

This version makes the receipt PDF show the same cumulative
Paid Amount and Balance as the invoice PDF by:

- Reusing load_invoice_context(invoice_id, db) for:
  - items
  - items_total
  - total_due
  - paid_amount (cumulative across all payments)
  - balance (remaining after ALL payments)

- Keeping `amount` for THIS receipt as this payment's instalment.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.fee.receipt import Receipt
from app.models.fee.payment import Payment
from app.models.fee.fee_invoice import FeeInvoice as Invoice
from app.models.student import Student
from app.schemas.fee.receipt import ReceiptOut
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

# ⬇️ we reuse the SAME loader that makes invoice PDFs correct
from app.services.pdf.context_loader import load_invoice_context
from app.services.pdf.renderer import render_receipt_pdf

logger = logging.getLogger("app.services.receipt_service")

RECEIPTS_DIR = Path("app/data/receipts")
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def _generate_receipt_no() -> str:
    return f"REC-{uuid.uuid4().hex[:10].upper()}"


class ReceiptService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def get_by_payment_id(self, payment_id: int) -> Optional[ReceiptOut]:
        """
        Return an existing receipt for the given payment_id, or None.
        """
        receipt = (
            self.db.query(Receipt)
            .filter(Receipt.payment_id == payment_id)
            .first()
        )
        return ReceiptOut.from_orm(receipt) if receipt else None

    def validate_payment_for_receipt(self, payment_id: int) -> Payment:
        """
        Ensure the payment exists, is linked to an invoice and student,
        and is in a paid/posted/captured state.
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Payment not found"},
            )

        # Resolve invoice robustly
        invoice = None

        # Relationship if present
        try:
            rel = getattr(payment, "invoice", None)
            if rel is not None:
                invoice = rel
        except Exception:
            invoice = None

        # Fallback: common FK names
        if invoice is None:
            inv_id = None
            for attr in ("fee_invoice_id", "invoice_id", "fee_invoice", "invoice"):
                try:
                    v = getattr(payment, attr, None)
                except Exception:
                    v = None

                if v is not None:
                    if isinstance(v, int):
                        inv_id = v
                        break
                    if hasattr(v, "id"):
                        inv_id = getattr(v, "id")
                        break

            if inv_id is not None:
                invoice = (
                    self.db.query(Invoice)
                    .filter(Invoice.id == inv_id)
                    .first()
                )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "not_found",
                    "message": "Invoice not found for payment",
                },
            )

        # Ensure invoice->student exists
        student = self.db.query(Student).filter(Student.id == invoice.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "not_found",
                    "message": "Student not found for invoice",
                },
            )

        # Payment status check
        valid_statuses = {"paid", "posted", "captured"}
        if hasattr(payment, "status"):
            if str(payment.status).lower() not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "invalid_state",
                        "message": "Payment is not in a paid/posted state",
                    },
                )
        elif hasattr(payment, "is_posted"):
            if not bool(payment.is_posted):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "invalid_state",
                        "message": "Payment is not posted",
                    },
                )

        return payment

    def _resolve_created_by(self, created_by: int | None) -> int:
        """
        Resolve a valid created_by user id (admin/clerk), creating a system user
        if necessary.
        """
        if created_by is not None:
            user = self.db.query(User).filter(User.id == created_by).first()
            if user:
                if user.role in ("admin", "clerk"):
                    return created_by
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "code": "forbidden",
                            "message": "Only admin or clerk can create receipts",
                        },
                    )

        # Try existing admin/clerk
        fallback_user = (
            self.db.query(User)
            .filter(User.role.in_(["admin", "clerk"]))
            .order_by(User.id.asc())
            .first()
        )
        if fallback_user:
            logger.debug(
                "resolve_created_by: using fallback user id=%s", fallback_user.id
            )
            return fallback_user.id

        # Create minimal system admin if needed
        try:
            sys_email = "system@example.com"
            existing = self.db.query(User).filter(User.email == sys_email).first()
            if existing:
                return existing.id

            pwd_hash = get_password_hash("system-default-password")
            sys_user = User(
                email=sys_email,
                hashed_password=pwd_hash,
                role="admin",
                is_active=True,
            )
            self.db.add(sys_user)
            self.db.flush()
            return sys_user.id
        except Exception as e:
            logger.exception(
                "resolve_created_by: failed to create system user: %s", e
            )

        logger.warning("resolve_created_by: fallback created_by=1")
        return 1

    def _compute_pdf_path(self, receipt_no: str) -> str:
        """
        Compute a deterministic absolute path for a receipt PDF.
        """
        try:
            base = settings.receipts_path()
        except Exception:
            base = RECEIPTS_DIR

        base = Path(base)
        base.mkdir(parents=True, exist_ok=True)

        filename = f"{receipt_no}.pdf"
        return str((base / filename).resolve())

    # ------------------------------------------------------------------
    # Main entry: create + render
    # ------------------------------------------------------------------
    def create_receipt_and_render(
        self,
        payment_id: int,
        receipt_no: str | None = None,
        created_by: int | None = None,
    ) -> ReceiptOut:
        """
        Create a new receipt for the given payment and render its PDF.

        IMPORTANT:
        - One receipt per payment (instalment).
        - For totals, we **trust invoice context** (same as invoice PDF):
          - items, items_total
          - total_due
          - paid_amount (cumulative)
          - balance
        - For this instalment, we still expose `amount` = payment.amount
        """
        # 1) Validate payment & relations
        payment = self.validate_payment_for_receipt(payment_id)

        # 2) Resolve invoice id using the same pattern as above
        invoice_id = getattr(payment, "fee_invoice_id", None) or getattr(
            payment, "invoice_id", None
        )
        if not invoice_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "not_found",
                    "message": "Payment is not linked to any invoice",
                },
            )

        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.id == invoice_id)
            .first()
        )
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Invoice not found"},
            )

        # 3) Load invoice context (this already knows about ALL payments)
        inv_ctx = load_invoice_context(invoice.id, self.db)

        # Items & item total from invoice context
        items = inv_ctx.get("items") or []
        items_total = float(inv_ctx.get("items_total") or 0.0)

        # Total due from context; fallback to invoice.amount_due
        raw_total_due = inv_ctx.get("total_due")
        if raw_total_due is None:
            raw_total_due = invoice.amount_due
        total_due = float(raw_total_due or 0.0)

        # ✅ Paid & balance directly from invoice context (cumulative)
        raw_paid_amount = inv_ctx.get("paid_amount")
        paid_amount = float(raw_paid_amount or 0.0)

        raw_balance = inv_ctx.get("balance")
        if raw_balance is not None:
            balance = float(raw_balance)
        else:
            balance = total_due - paid_amount

        # 4) Ensure receipt_no & created_by
        receipt_no = receipt_no or _generate_receipt_no()
        created_by_id = self._resolve_created_by(created_by)

        # 5) Idempotency: one receipt per payment
        existing = (
            self.db.query(Receipt)
            .filter(Receipt.payment_id == payment_id)
            .first()
        )
        if existing:
            receipt = existing
        else:
            pdf_path_guess = self._compute_pdf_path(receipt_no)
            receipt = Receipt(
                payment_id=payment_id,
                receipt_no=receipt_no,
                pdf_path=str(pdf_path_guess),
                created_by=created_by_id,
            )
            self.db.add(receipt)
            try:
                self.db.flush()
            except IntegrityError as e:
                logger.exception("Duplicate receipt_no? %s", e)
                raise

        # 6) Build context for receipt template
        student = invoice.student  # for label only
        issued_dt: datetime = receipt.created_at or datetime.utcnow()

        ctx = {
            # receipt
            "receipt_no": receipt.receipt_no,
            "receipt_id": receipt.id,
            "receipt": receipt,
            "issued_date": issued_dt.isoformat(),

            # student / invoice
            "student_name": getattr(student, "name", None),
            "student": student,
            "invoice_no": getattr(invoice, "invoice_no", None),
            "invoice": invoice,

            # invoice-level financials (from invoice context — cumulative)
            "items": items,
            "items_total": items_total,
            "total_due": total_due,
            "paid_amount": paid_amount,  # ✅ cumulative
            "balance": balance,          # ✅ consistent with invoice PDF

            # this instalment only
            "amount": float(payment.amount or 0.0),
            "payment": payment,
        }

        # 7) Render PDF
        pdf_path = self._compute_pdf_path(receipt.receipt_no)
        try:
            render_receipt_pdf(ctx, str(pdf_path))
        except Exception as e:
            logger.exception(
                "Failed to render receipt PDF for payment_id=%s, receipt_id=%s: %s",
                payment_id,
                getattr(receipt, "id", None),
                e,
            )
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "render_failed", "message": str(e)},
            )

        # 8) Persist pdf_path and commit
        receipt.pdf_path = str(pdf_path)
        try:
            self.db.add(receipt)
            self.db.commit()
            self.db.refresh(receipt)
        except Exception as e:
            logger.exception("Failed to commit receipt after render: %s", e)
            try:
                self.db.rollback()
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "db_error",
                    "message": "Failed to persist receipt after rendering",
                },
            )

        return ReceiptOut.from_orm(receipt)
