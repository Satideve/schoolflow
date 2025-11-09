# backend/app/schemas/fee/invoice.py

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any

class InvoiceCreate(BaseModel):
    student_id: int
    invoice_no: str
    period: str
    amount_due: Decimal
    due_date: datetime
    payment: Optional[Dict] = None  # optional, preserved

class InvoiceOut(InvoiceCreate):
    id: int
    status: str
    created_at: datetime

    # --- NEW: fields used by PDFs, now exposed in API for parity ---
    items_total: Optional[float] = None
    total_due: Optional[float] = None
    paid_amount: Optional[float] = None
    balance: Optional[float] = None
    items: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True
