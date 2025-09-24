# backend/app/repositories/fee_repo.py

"""
Repository methods for fee module.
"""

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

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
    db: Session, student_id: int, period: str, amount_due: Decimal, due_date: datetime
) -> FeeInvoice:
    inv = FeeInvoice(
        student_id=student_id,
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
    db: Session, payment_id: int, receipt_no: str, pdf_path: str
) -> Receipt:
    receipt = Receipt(
        payment_id=payment_id,
        receipt_no=receipt_no,
        pdf_path=pdf_path
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt
