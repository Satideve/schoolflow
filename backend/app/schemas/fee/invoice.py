# schoolflow/backend/app/schemas/fee/invoice.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class InvoiceCreate(BaseModel):
    student_id: int
    period: str
    amount_due: Decimal
    due_date: datetime

class InvoiceOut(InvoiceCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
