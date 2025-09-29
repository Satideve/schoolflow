# backend/app/services/fee/receipt_service.py

"""
Receipt creation and PDF rendering service.

This module provides a reusable class `ReceiptService` that:
- Validates the payment→invoice→student relationship before creating a receipt
- Creates a receipt record in the database for a given payment_id
- Records the user who created the receipt (created_by)
- Generates a canonical receipt number if none is provided
- Computes the final PDF path
- Loads rendering context from the database
- Renders the receipt PDF using the standard template and options

This service is the canonical path for generating receipts across all flows.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.fee.receipt import Receipt
from app.models.fee.payment import Payment
from app.models.fee.fee_invoice import FeeInvoice as Invoice
from app.models.student import Student  # adjust if your student model path differs
from app.ops.create_receipt import main as ops_create_and_render
from app.schemas.fee.receipt import ReceiptOut

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
        and the payment is in a paid/posted state.
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Payment not found"},
            )

        invoice = self.db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Invoice not found for payment"},
            )

        student = self.db.query(Student).filter(Student.id == invoice.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Student not found for invoice"},
            )

        # Enforce payment status; adjust to your schema
        valid_statuses = {"paid", "posted"}
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

    def create_receipt_and_render(
        self,
        payment_id: int,
        receipt_no: str | None = None,
        created_by: int | None = None,
    ) -> ReceiptOut:
        """
        1. Validate payment→invoice→student relationship.
        2. Persist a new Receipt row (with blank pdf_path and created_by).
        3. Call the ops script to generate/render the PDF; it returns the file path.
        4. Update the Receipt.pdf_path, commit, refresh, and return a ReceiptOut.
        """
        # Step 1: validation
        self.validate_payment_for_receipt(payment_id)

        # ensure receipt_no
        receipt_no = receipt_no or _generate_receipt_no()

        # Step 2: insert with placeholder
        new_receipt = Receipt(
            payment_id=payment_id,
            receipt_no=receipt_no,
            pdf_path="",
            created_by=created_by,
        )
        self.db.add(new_receipt)
        self.db.flush()  # populates new_receipt.id

        # Step 3: generate PDF via the ops script
        generated_pdf_path = ops_create_and_render(new_receipt.id)

        # Step 4: persist the actual path
        new_receipt.pdf_path = generated_pdf_path
        self.db.commit()
        self.db.refresh(new_receipt)

        return ReceiptOut.from_orm(new_receipt)
