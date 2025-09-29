# backend/app/schemas/fee/receipt.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReceiptCreate(BaseModel):
    payment_id: int
    receipt_no: str

class ReceiptOut(ReceiptCreate):
    id: int
    pdf_path: str
    created_at: datetime
    created_by: int   # NEW FIELD for audit trail

    class Config:
        from_attributes = True
