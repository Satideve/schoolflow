# schoolflow/backend/app/schemas/fee/invoice.py

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict

class InvoiceCreate(BaseModel):
    student_id: int
    invoice_no: str
    period: str
    amount_due: Decimal
    due_date: datetime
    payment: Optional[Dict] = None  # <-- added field, optional to preserve existing functionality

class InvoiceOut(InvoiceCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
