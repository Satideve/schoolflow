# backend/app/repositories/invoice_repo.py

"""
Repository methods for invoice entity.

This module provides focused helpers used by invoice-related services and
routers. Keep this separate from fee_repo which contains broader fee-related
helpers (payments, receipts, plans, components).
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from app.models.fee.fee_invoice import FeeInvoice


def create_invoice(
    db: Session,
    student_id: int,
    invoice_no: str,
    period: str,
    amount_due: Decimal,
    due_date: datetime,
) -> FeeInvoice:
    """
    Persist a new FeeInvoice in the database.

    Best-practice behavior added:
      - Normalize invoice_no (trim) to avoid accidental whitespace collisions.
      - Attempt insert and, on IntegrityError due to unique constraint,
        rollback and return the existing invoice (idempotent behavior).
      - Caller can still commit/refresh when needed; this function performs
        commit/refresh for convenience but remains safe against races.
    """
    # Basic normalization to avoid trivial collisions
    if invoice_no is not None:
        invoice_no = str(invoice_no).strip()

    inv = FeeInvoice(
        student_id=student_id,
        invoice_no=invoice_no,
        period=period,
        amount_due=amount_due,
        due_date=due_date,
    )
    db.add(inv)
    try:
        db.commit()
        db.refresh(inv)
        return inv
    except IntegrityError:
        # Another transaction created the same invoice_no concurrently
        # Roll back this session and return the canonical existing row (idempotent).
        db.rollback()
        existing = get_invoice_by_no(db, invoice_no)
        if existing:
            return existing
        # If no existing row found (unexpected), re-raise to surface problem
        raise


def get_invoice(db: Session, invoice_id: int) -> Optional[FeeInvoice]:
    """
    Fetch a single invoice by ID.
    """
    return db.query(FeeInvoice).filter(FeeInvoice.id == invoice_id).first()


def get_invoice_by_no(db: Session, invoice_no: str) -> Optional[FeeInvoice]:
    """
    Fetch a single invoice by its invoice_no.
    """
    if invoice_no is not None:
        invoice_no = str(invoice_no).strip()
    return db.query(FeeInvoice).filter(FeeInvoice.invoice_no == invoice_no).first()


def list_invoices(db: Session) -> List[FeeInvoice]:
    """
    Return all invoices, ordered by ID to ensure deterministic ordering in tests.
    """
    return db.query(FeeInvoice).order_by(FeeInvoice.id).all()


def mark_invoice_paid(db: Session, invoice: FeeInvoice) -> FeeInvoice:
    """
    Update invoice status to 'paid'.
    """
    invoice.status = "paid"
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
