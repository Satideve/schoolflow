# backend/app/api/v1/routers/fees/payments.py
from fastapi import APIRouter, Request, Header, Depends, HTTPException
from app.services.payments.fake_adapter import FakePaymentAdapter
from app.services.messaging.fake_adapter import FakeMessagingAdapter
from app.services.fees_service import FeesService
from app.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

@router.post("/create-order/{invoice_id}")
def create_order(invoice_id: int, db: Session = Depends(get_db)):
    # Simplified: find invoice then create order
    invoice = db.query(__import__("app.models.fee.fee_invoice", fromlist=["FeeInvoice"]).FeeInvoice).get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"Invoice not found"})
    svc = FeesService(db=db, payment_gateway=FakePaymentAdapter(), messaging=FakeMessagingAdapter())
    order = svc.create_payment_order(invoice_id, invoice.amount_due)
    return {"order": order}

@router.post("/webhook")
async def webhook(request: Request, x_signature: str | None = Header(None), db: Session = Depends(get_db)):
    body = await request.body()
    svc = FeesService(db=db, payment_gateway=FakePaymentAdapter(), messaging=FakeMessagingAdapter())
    try:
        result = svc.handle_webhook_mark_paid(body, x_signature or "")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail={"code":"webhook_failed","message": str(e)})
