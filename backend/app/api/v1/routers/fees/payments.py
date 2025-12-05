# schoolflow/backend/app/api/v1/routers/fees/payments.py
from fastapi import APIRouter, Request, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from uuid import uuid4
from typing import Optional

from app.services.payments.fake_adapter import FakePaymentAdapter
from app.services.messaging.fake_adapter import FakeMessagingAdapter
from app.services.fee.fees_service import FeesService
from app.db.session import get_db

from app.models.fee.fee_invoice import FeeInvoice
from app.models.fee.payment import Payment
from app.services.fee.receipt_service import ReceiptService
from app.api.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


# ---------- EXISTING ORDER-CREATION ENDPOINT (kept as-is) ----------
@router.post("/create-order/{invoice_id}")
def create_order(invoice_id: int, db: Session = Depends(get_db)):
  # Simplified: find invoice then create order
  invoice = (
      db.query(
          __import__("app.models.fee.fee_invoice", fromlist=["FeeInvoice"]).FeeInvoice
      ).get(invoice_id)
  )
  if not invoice:
      raise HTTPException(
          status_code=404,
          detail={"code": "not_found", "message": "Invoice not found"},
      )
  svc = FeesService(
      db=db,
      payment_gateway=FakePaymentAdapter(),
      messaging=FakeMessagingAdapter(),
  )
  order = svc.create_payment_order(invoice_id, invoice.amount_due)
  return {"order": order}


# ---------- NEW: MANUAL PAYMENT WITH ONE RECEIPT PER INSTALMENT ----------
from pydantic import BaseModel


class ManualPaymentPayload(BaseModel):
  amount: float
  provider: str = "offline"
  note: Optional[str] = None


@router.post("/manual/{invoice_id}")
def create_manual_payment(
  invoice_id: int,
  payload: ManualPaymentPayload,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
  """
  Create a manual payment *and* a receipt for this invoice.

  - Each call creates:
      1) a Payment row (success)
      2) a Receipt row + rendered PDF for that payment
  - RBAC:
      - admin/clerk: can pay any invoice
      - student/parent: only if mapped to that invoice's student_id
  """

  # 1) Find invoice
  invoice = db.query(FeeInvoice).get(invoice_id)
  if not invoice:
      raise HTTPException(
          status_code=404,
          detail={"code": "not_found", "message": "Invoice not found"},
      )

  # 2) RBAC / ownership
  role = getattr(current_user, "role", None)
  if role in {"student", "parent"}:
      # must be linked to this invoice's student_id
      if getattr(current_user, "student_id", None) != invoice.student_id:
          raise HTTPException(
              status_code=403,
              detail={"code": "forbidden", "message": "Not allowed to pay this invoice"},
          )
  elif role not in {"admin", "clerk", "accountant"}:
      raise HTTPException(
          status_code=403,
          detail={"code": "forbidden", "message": "Not authorized"},
      )

  # 3) Basic amount guard
  try:
      amt = Decimal(str(payload.amount))
  except Exception:
      raise HTTPException(
          status_code=400,
          detail={"code": "invalid_amount", "message": "Invalid amount"},
      )

  if amt <= 0:
      raise HTTPException(
          status_code=400,
          detail={"code": "invalid_amount", "message": "Amount must be > 0"},
      )

  # 4) Create Payment row (mark as success)
  provider = payload.provider or "offline"
  provider_txn_id = f"MANUAL-{invoice_id}-{uuid4().hex[:10]}"

  payment = Payment(
      fee_invoice_id=invoice.id,
      provider=provider,
      provider_txn_id=provider_txn_id,
      amount=amt,
      status="success",
      # idempotency_key left as None for manual demo payments
  )
  db.add(payment)
  db.flush()  # get payment.id

  # We let FeesService or context-loader compute totals from Payment rows,
  # so we don't need to mutate invoice.amount_due / paid_amount here.

  # 5) Create a receipt *for this instalment* and render its PDF
  receipt_service = ReceiptService(db)

  # Simple generated receipt number (unique-ish and readable)
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

  # Frontend doesn't currently use this response, but we return useful info.
  return {
      "status": "ok",
      "invoice_id": invoice.id,
      "payment_id": payment.id,
      "receipt_id": receipt.id,
      "receipt_no": receipt.receipt_no,
  }


# ---------- EXISTING WEBHOOK ENDPOINT (kept, with wkhtmltopdf options) ----------
@router.post("/webhook")
async def webhook(
  request: Request,
  x_signature: str | None = Header(None),
  db: Session = Depends(get_db),
):
  body = await request.body()

  # ✅ Inject wkhtmltopdf options to avoid QPainter errors
  pdf_options = {
      "header-right": "Page [page] of [topage]",
      "encoding": "UTF-8",
      "disable-smart-shrinking": "",
      "no-outline": "",
      "page-size": "A4",
  }

  svc = FeesService(
      db=db,
      payment_gateway=FakePaymentAdapter(),
      messaging=FakeMessagingAdapter(),
  )
  try:
      result = svc.handle_webhook_mark_paid(body, x_signature or "", pdf_options)
      return result
  except Exception as e:
      raise HTTPException(
          status_code=400,
          detail={"code": "webhook_failed", "message": str(e)},
      )
