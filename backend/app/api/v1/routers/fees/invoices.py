# backend/app/api/v1/routers/fees/invoices.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from app.db.session import get_db
from app.schemas.fee.plan import InvoiceCreate
from app.services.fees_service import FeesService
from app.services.payments.fake_adapter import FakePaymentAdapter
from app.services.messaging.fake_adapter import FakeMessagingAdapter

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])

@router.post("/")
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    # compute amount based on fee assignment or plan - simplified: use seed value or param
    amount = Decimal("5000.00")
    svc = FeesService(db=db, payment_gateway=FakePaymentAdapter(), messaging=FakeMessagingAdapter())
    inv = svc.generate_invoice_for_student(student_id=payload.student_id, period=payload.period, amount=amount, due_date=datetime.combine(payload.due_date, datetime.min.time()))
    return {"id": inv.id, "student_id": inv.student_id, "amount_due": float(inv.amount_due), "period": inv.period, "due_date": inv.due_date.isoformat(), "status": inv.status}
