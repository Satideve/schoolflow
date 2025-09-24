# backend/app/services/fee/receipt_service.py

"""
Receipt creation and PDF rendering service.

This module provides a reusable class `ReceiptService` that:
- Creates a receipt record in the database for a given payment_id
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

from app.models.fee.receipt import Receipt
from app.repositories.fee_repo import create_receipt
from app.services.pdf.context_loader import load_receipt_context
from app.services.pdf.renderer import render_receipt_pdf
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

    def create_receipt_and_render(
        self,
        payment_id: int,
        receipt_no: str | None = None
    ) -> ReceiptOut:
        """
        1. Persist a new Receipt row (with blank pdf_path).
        2. Call the ops script to generate/render the PDF; it returns the file path.
        3. Update the Receipt.pdf_path, commit, refresh, and return a ReceiptOut.
        """
        # ensure receipt_no
        receipt_no = receipt_no or _generate_receipt_no()

        # Step 1: insert with placeholder
        new_receipt = Receipt(payment_id=payment_id, receipt_no=receipt_no, pdf_path="")
        self.db.add(new_receipt)
        self.db.flush()  # populates new_receipt.id

        # Step 2: generate PDF via the ops script
        generated_pdf_path = ops_create_and_render(new_receipt.id)

        # Step 3: persist the actual path
        new_receipt.pdf_path = generated_pdf_path
        self.db.commit()
        self.db.refresh(new_receipt)

        return ReceiptOut.from_orm(new_receipt)
