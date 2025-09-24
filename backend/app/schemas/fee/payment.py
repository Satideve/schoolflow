# schoolflow/backend/app/schemas/fee/payment.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional

class PaymentCreate(BaseModel):
    fee_invoice_id: int
    provider: str
    provider_txn_id: str
    amount: Decimal
    idempotency_key: Optional[str] = None

class PaymentOut(PaymentCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
