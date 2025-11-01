# backend/app/repositories/fee_repo.py
"""
Repository methods for fee module.

Contains helper functions for fee-plans, components, assignments, payments,
and receipts. These are used across services and tests.
"""

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import Optional
import uuid

from app.models.fee.fee_plan import FeePlan
from app.models.fee.fee_component import FeeComponent
from app.models.fee.fee_plan_component import FeePlanComponent
from app.models.fee.fee_assignment import FeeAssignment
from app.models.fee.fee_invoice import FeeInvoice
from app.models.fee.payment import Payment
from app.models.fee.receipt import Receipt


def create_fee_plan(
    db: Session, name: str, academic_year: str, frequency: str
) -> FeePlan:
    plan = FeePlan(name=name, academic_year=academic_year, frequency=frequency)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_fee_plan(db: Session, plan_id: int) -> FeePlan | None:
    return db.query(FeePlan).filter(FeePlan.id == plan_id).first()


def list_fee_plans(db: Session) -> list[FeePlan]:
    return db.query(FeePlan).all()


def create_fee_component(
    db: Session, name: str, description: str | None = None
) -> FeeComponent:
    comp = FeeComponent(name=name, description=description)
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


def add_component_to_plan(
    db: Session, fee_plan_id: int, fee_component_id: int, amount: Decimal
) -> FeePlanComponent:
    item = FeePlanComponent(
        fee_plan_id=fee_plan_id,
        fee_component_id=fee_component_id,
        amount=amount
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_fee_assignment(
    db: Session, student_id: int, fee_plan_id: int, concession: Decimal | None = None, note: str | None = None
) -> FeeAssignment:
    assignment = FeeAssignment(
        student_id=student_id,
        fee_plan_id=fee_plan_id,
        concession=concession or 0,
        note=note
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def create_invoice(
    db: Session,
    student_id: int,
    period: str,
    amount_due: Decimal,
    due_date: datetime,
    invoice_no: Optional[str] = None,
) -> FeeInvoice:
    """
    Create a FeeInvoice. `invoice_no` is optional for backward compatibility:
    - If caller supplies invoice_no, that value is used.
    - If not supplied, a unique invoice_no will be generated (INV-XXXXXXXX).
    This prevents NOT NULL constraint failures for code paths that didn't set invoice_no.
    """
    if not invoice_no:
        invoice_no = f"INV-{uuid.uuid4().hex[:8].upper()}"

    inv = FeeInvoice(
        student_id=student_id,
        invoice_no=invoice_no,
        period=period,
        amount_due=amount_due,
        due_date=due_date
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def create_payment(
    db: Session,
    fee_invoice_id: int,
    provider: str,
    provider_txn_id: str,
    amount: Decimal,
    status: str,
    idempotency_key: str | None = None
) -> Payment:
    payment = Payment(
        fee_invoice_id=fee_invoice_id,
        provider=provider,
        provider_txn_id=provider_txn_id,
        amount=amount,
        status=status,
        idempotency_key=idempotency_key
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def mark_invoice_paid(db: Session, invoice: FeeInvoice) -> FeeInvoice:
    invoice.status = "paid"
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def create_receipt(
    db: Session, payment_id: int, receipt_no: str, pdf_path: str, created_by: int | None = None
) -> Receipt:
    """
    Create and persist a Receipt.

    - `created_by` is optional for backward compatibility.
    - If not provided, fall back to a safe system/admin id (1) so NOT NULL DB constraints are satisfied.
      (Higher-level code should pass a real user id when available.)
    """
    created_by_val = created_by if created_by is not None else 1

    receipt = Receipt(
        payment_id=payment_id,
        receipt_no=receipt_no,
        pdf_path=pdf_path,
        created_by=created_by_val,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


# ----------------------------
# Convenience listing / getters
# ----------------------------
def list_receipts(db: Session, limit: int | None = None) -> list[Receipt]:
    """
    Return receipts ordered by id descending (most recent first).
    Optionally limit the number returned.
    """
    q = db.query(Receipt).order_by(Receipt.id.desc())
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def get_receipt_by_id(db: Session, receipt_id: int) -> Receipt | None:
    return db.query(Receipt).filter(Receipt.id == receipt_id).first()


def list_payments(db: Session, limit: int | None = None) -> list[Payment]:
    q = db.query(Payment).order_by(Payment.id.desc())
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def get_payment_by_id(db: Session, payment_id: int) -> Payment | None:
    return db.query(Payment).filter(Payment.id == payment_id).first()


def list_invoices(db: Session, limit: int | None = None) -> list[FeeInvoice]:
    q = db.query(FeeInvoice).order_by(FeeInvoice.id.desc())
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def get_invoice_by_id(db: Session, invoice_id: int) -> FeeInvoice | None:
    return db.query(FeeInvoice).filter(FeeInvoice.id == invoice_id).first()
