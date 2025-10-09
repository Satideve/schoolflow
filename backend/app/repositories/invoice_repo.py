# backend/app/repositories/invoice_repo.py

"""
Repository methods for invoice entity.

This module provides focused helpers used by invoice-related services and
routers. Keep this separate from fee_repo which contains broader fee-related
helpers (payments, receipts, plans, components).
"""

from sqlalchemy.orm import Session
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
    The caller is expected to handle commit/refresh if needed, but for
    convenience this function commits and refreshes the instance.
    """
    inv = FeeInvoice(
        student_id=student_id,
        invoice_no=invoice_no,
        period=period,
        amount_due=amount_due,
        due_date=due_date,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def get_invoice(db: Session, invoice_id: int) -> Optional[FeeInvoice]:
    """
    Fetch a single invoice by ID.
    """
    return db.query(FeeInvoice).filter(FeeInvoice.id == invoice_id).first()


def get_invoice_by_no(db: Session, invoice_no: str) -> Optional[FeeInvoice]:
    """
    Fetch a single invoice by its invoice_no.
    """
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
