# backend/app/api/v1/routers/fees/payments.py

from fastapi import APIRouter, Request, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from uuid import uuid4
from typing import Optional

from pydantic import BaseModel

from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User

from app.models.fee.fee_invoice import FeeInvoice
from app.models.fee.payment import Payment

from app.services.fee.fees_service import FeesService
from app.services.fee.receipt_service import ReceiptService
from app.services.messaging.fake_adapter import FakeMessagingAdapter
from app.services.payments.factory import get_payment_gateway

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


# -------------------------------------------------------------------
# ORDER CREATION (ONLINE / GATEWAY)
# -------------------------------------------------------------------
@router.post("/create-order/{invoice_id}")
def create_order(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    invoice = db.query(FeeInvoice).get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Invoice not found"},
        )

    svc = FeesService(
        db=db,
        payment_gateway=get_payment_gateway(),
        messaging=FakeMessagingAdapter(),
    )

    order = svc.create_payment_order(invoice.id, invoice.amount_due)
    return {"order": order}


# -------------------------------------------------------------------
# MANUAL PAYMENT (OFFLINE / CASH / CHEQUE)
# -------------------------------------------------------------------
class ManualPaymentPayload(BaseModel):
    amount: float
    provider: str = "manual"
    note: Optional[str] = None


@router.post("/manual/{invoice_id}")
def create_manual_payment(
    invoice_id: int,
    payload: ManualPaymentPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Invoice
    invoice = db.query(FeeInvoice).get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Invoice not found"},
        )

    # 2. RBAC
    role = getattr(current_user, "role", None)
    if role in {"student", "parent"}:
        if getattr(current_user, "student_id", None) != invoice.student_id:
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Not allowed"},
            )
    elif role not in {"admin", "clerk", "accountant"}:
        raise HTTPException(
            status_code=403,
            detail={"code": "forbidden", "message": "Not authorized"},
        )

    # 3. Amount validation
    try:
        amount = Decimal(str(payload.amount))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_amount", "message": "Invalid amount"},
        )

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_amount", "message": "Amount must be > 0"},
        )

    # 4. Create Payment (VALID STATE)
    payment = Payment(
        fee_invoice_id=invoice.id,
        provider=payload.provider or "manual",
        provider_txn_id=f"MANUAL-{invoice.id}-{uuid4().hex[:10]}",
        amount=amount,
        status="paid",  # 🔑 MUST be paid/posted
    )

    db.add(payment)
    db.flush()  # get payment.id

    # 5. Create Receipt + PDF
    receipt_service = ReceiptService(db)
    receipt_no = f"REC-{uuid4().hex[:8].upper()}"

    try:
        receipt = receipt_service.create_receipt_and_render(
            payment_id=payment.id,
            receipt_no=receipt_no,
            created_by=current_user.id,
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={"code": "receipt_failed", "message": str(e)},
        )

    return {
        "status": "ok",
        "invoice_id": invoice.id,
        "payment_id": payment.id,
        "receipt_id": receipt.id,
        "receipt_no": receipt.receipt_no,
    }


# -------------------------------------------------------------------
# WEBHOOK (ONLINE GATEWAYS)
# -------------------------------------------------------------------
@router.post("/webhook")
async def webhook(
    request: Request,
    x_signature: str | None = Header(None),
    db: Session = Depends(get_db),
):
    body = await request.body()

    pdf_options = {
        "header-right": "Page [page] of [topage]",
        "encoding": "UTF-8",
        "disable-smart-shrinking": "",
        "no-outline": "",
        "page-size": "A4",
    }

    svc = FeesService(
        db=db,
        payment_gateway=get_payment_gateway(),
        messaging=FakeMessagingAdapter(),
    )

    try:
        return svc.handle_webhook_mark_paid(
            body,
            x_signature or "",
            pdf_options,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "webhook_failed", "message": str(e)},
        )
