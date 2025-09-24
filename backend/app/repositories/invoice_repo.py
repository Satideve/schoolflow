# backend/app/repositories/invoice_repo.py

"""
Repository methods for invoice entity.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from app.models.fee.fee_invoice import FeeInvoice


def create_invoice(
    db: Session,
    student_id: int,
    period: str,
    amount_due: Decimal,
    due_date: datetime,
) -> FeeInvoice:
    """
    Persist a new FeeInvoice in the database.
    """
    inv = FeeInvoice(
        student_id=student_id,
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


def list_invoices(db: Session) -> List[FeeInvoice]:
    """
    Return all invoices.
    """
    return db.query(FeeInvoice).all()


def mark_invoice_paid(db: Session, invoice: FeeInvoice) -> FeeInvoice:
    """
    Update invoice status to 'paid'.
    """
    invoice.status = "paid"
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
