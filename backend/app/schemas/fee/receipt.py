# backend/app/schemas/fee/receipt.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class ReceiptCreate(BaseModel):
    payment_id: int
    receipt_no: str


class ReceiptOut(ReceiptCreate):
    id: int
    pdf_path: str
    created_at: datetime
    created_by: Optional[int]   # allow null/None for older receipts or system-generated ones

    # extra, derived fields
    invoice_id: Optional[int] = None
    amount: Optional[Decimal] = None

    class Config:
        from_attributes = True
