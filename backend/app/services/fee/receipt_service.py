# backend/app/services/fee/receipt_service.py
"""
Receipt creation and PDF rendering service.

This module provides a reusable class `ReceiptService` that:
- Validates the payment→invoice→student relationship before creating a receipt
- Creates a receipt record in the database for a given payment_id
- Records the user who created the receipt (created_by)
- Generates a canonical receipt number if none is provided
- Computes the final PDF path (persisted BEFORE rendering so other parts can find it)
- Loads rendering context from the database
- Renders the receipt PDF using the standard template and options

Key change (robustness): set `Receipt.pdf_path` to a deterministic path *before*
calling the rendering op. This ensures the DB always contains the final path
and avoids races where another request tries to download the receipt while
the rendering is happening. The rendering op still re-renders the file at the
path we choose.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.fee.receipt import Receipt
from app.models.fee.payment import Payment
from app.models.fee.fee_invoice import FeeInvoice as Invoice
from app.models.student import Student
from app.ops.create_receipt import main as ops_create_and_render
from app.schemas.fee.receipt import ReceiptOut
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

logger = logging.getLogger("app.services.receipt_service")

# Keep an on-disk receipts dir default for local runs (tests / dev)
RECEIPTS_DIR = Path("app/data/receipts")
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def _generate_receipt_no() -> str:
    return f"REC-{uuid.uuid4().hex[:10].upper()}"


class ReceiptService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_payment_id(self, payment_id: int) -> ReceiptOut | None:
        """
        Return an existing receipt for the given payment_id, or None.
        """
        receipt = (
            self.db.query(Receipt)
            .filter(Receipt.payment_id == payment_id)
            .one_or_none()
        )
        return ReceiptOut.from_orm(receipt) if receipt else None

    def validate_payment_for_receipt(self, payment_id: int) -> Payment:
        """
        Ensure the payment exists, is linked to an invoice, that invoice belongs to a student,
        and the payment is in a paid/posted/captured state.

        This function is defensive about how the FK is named on Payment (some code uses
        `fee_invoice_id`, others `invoice_id`) and will use the relationship `payment.invoice`
        if it is populated.
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Payment not found"},
            )

        # Resolve invoice robustly:
        invoice = None

        # 1) Prefer relationship if loaded / available
        try:
            rel = getattr(payment, "invoice", None)
            if rel is not None:
                invoice = rel
        except Exception:
            invoice = None

        # 2) If relationship not present, try common FK column names
        if invoice is None:
            inv_id = None
            # common variants we may encounter
            for attr in ("fee_invoice_id", "invoice_id", "fee_invoice", "invoice"):
                try:
                    v = getattr(payment, attr, None)
                except Exception:
                    v = None
                # if attribute is an integer PK
                if v is not None:
                    if isinstance(v, int):
                        inv_id = v
                        break
                    # if v is an object (relationship), try to read its id
                    if hasattr(v, "id"):
                        inv_id = getattr(v, "id")
                        break
            if inv_id is not None:
                invoice = self.db.query(Invoice).filter(Invoice.id == inv_id).first()

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Invoice not found for payment"},
            )

        # Ensure invoice -> student exists
        student = self.db.query(Student).filter(Student.id == invoice.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Student not found for invoice"},
            )

        # Enforce payment status; adjust to your schema
        valid_statuses = {"paid", "posted", "captured"}
        if hasattr(payment, "status"):
            if str(payment.status).lower() not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "invalid_state", "message": "Payment is not in a paid/posted state"},
                )
        elif hasattr(payment, "is_posted"):
            if not bool(payment.is_posted):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "invalid_state", "message": "Payment is not posted"},
                )

        return payment

    def _resolve_created_by(self, created_by: int | None) -> int:
        """
        Ensures a valid created_by id for the Receipt.created_by field.

        Strategy:
        1. If created_by provided and user exists -> use it (must be admin/clerk)
        2. Else find an admin or clerk user and use it
        3. Else create a small 'system' admin user
        4. Fallback to 1
        """
        if created_by is not None:
            user = self.db.query(User).filter(User.id == created_by).first()
            if user:
                if user.role in ("admin", "clerk"):
                    return created_by
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={"code": "forbidden", "message": "Only admin or clerk can create receipts"},
                    )

        # Try to use an existing admin or clerk user
        fallback_user = (
            self.db.query(User)
            .filter(User.role.in_(["admin", "clerk"]))
            .order_by(User.id.asc())
            .first()
        )
        if fallback_user:
            logger.debug("resolve_created_by: using fallback user id=%s", fallback_user.id)
            return fallback_user.id

        # Create system admin if no admin/clerk exists
        try:
            sys_email = "system@example.com"
            existing = self.db.query(User).filter(User.email == sys_email).first()
            if existing:
                return existing.id

            pwd_hash = get_password_hash("system-default-password")
            sys_user = User(email=sys_email, hashed_password=pwd_hash, role="admin", is_active=True)
            self.db.add(sys_user)
            self.db.flush()
            return sys_user.id
        except Exception as e:
            logger.exception("resolve_created_by: failed to create system user: %s", e)

        logger.warning("resolve_created_by: fallback created_by=1")
        return 1

    def _compute_pdf_path(self, receipt_no: str, receipt_id: int | None = None) -> str:
        """
        Compute a deterministic absolute path for a receipt PDF and return it as string.

        Preference:
         - Use settings.receipts_path() when available (resolves using settings.base_dir).
         - Fallback to repository-local RECEIPTS_DIR.
         - Filename: <receipt_no>.pdf (avoid embedding DB id in name so file names are stable).
        """
        try:
            base = settings.receipts_path()
        except Exception:
            base = RECEIPTS_DIR

        # Ensure path exists
        base = Path(base)
        base.mkdir(parents=True, exist_ok=True)

        filename = f"{receipt_no}.pdf"
        return str((base / filename).resolve())

    def create_receipt_and_render(
        self,
        payment_id: int,
        receipt_no: str | None = None,
        created_by: int | None = None,
    ) -> ReceiptOut:
        """
        1. Validate payment→invoice→student relationship.
        2. Persist a new Receipt row with a deterministic pdf_path (so DB is consistent).
        3. Call the ops script to generate/render the PDF; it returns the file path.
        4. Update the Receipt.pdf_path (if ops changed it), commit, refresh, and return a ReceiptOut.
        """
        # Step 1: validation
        payment = self.validate_payment_for_receipt(payment_id)

        # ensure receipt_no
        receipt_no = receipt_no or _generate_receipt_no()

        # Resolve created_by to a non-None, valid user id
        created_by_id = self._resolve_created_by(created_by)

        # Step 2: compute deterministic pdf path and insert the Receipt
        pdf_path_guess = self._compute_pdf_path(receipt_no)

        new_receipt = Receipt(
            payment_id=payment_id,
            receipt_no=receipt_no,
            pdf_path=str(pdf_path_guess),
            created_by=created_by_id,
        )
        self.db.add(new_receipt)
        # Flush to populate new_receipt.id (but don't commit yet so we can rollback if render fails)
        self.db.flush()

        # Step 3: generate PDF via the ops script (isolated process-level rendering)
        try:
            # ops_create_and_render expects a receipt_id and will re-render at receipt.pdf_path (which we just set)
            generated_pdf_path = ops_create_and_render(new_receipt.id)
        except Exception as e:
            # If PDF generation fails, rollback addition of receipt to keep DB consistent
            self.db.rollback()
            logger.exception("create_receipt_and_render: PDF generation failed for receipt_id=%s: %s", new_receipt.id, e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "render_failed", "message": str(e)},
            )

        # Step 4: persist the actual path (ops may have returned a path)
        try:
            # Prefer the path returned by ops if non-empty, else keep the one we set
            if generated_pdf_path:
                new_receipt.pdf_path = str(generated_pdf_path)
            else:
                # ensure at least the guessed path is persisted
                new_receipt.pdf_path = str(pdf_path_guess)
            self.db.commit()
            self.db.refresh(new_receipt)
        except Exception:
            # If commit fails, try to rollback and raise a 500-like error
            try:
                self.db.rollback()
            except Exception:
                pass
            logger.exception("create_receipt_and_render: failed to commit receipt after rendering for id=%s", new_receipt.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "db_error", "message": "Failed to persist receipt after rendering"},
            )

        return ReceiptOut.from_orm(new_receipt)
