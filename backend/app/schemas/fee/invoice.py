# backend/app/schemas/fee/invoice.py

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any


class InvoiceCreate(BaseModel):
    """
    Input schema for creating an invoice.

    Notes:
    - amount_due is treated as an *extra* / top-up amount.
      The backend will:
        * compute the base amount from fee plan / components
        * then add this extra amount on top.
      If omitted or 0, only the plan-derived amount is used.
    """
    student_id: int
    invoice_no: str
    period: str
    due_date: datetime
    amount_due: Optional[Decimal] = None
    payment: Optional[Dict] = None  # optional, preserved


class InvoiceOut(InvoiceCreate):
    id: int
    status: str
    created_at: datetime

    # --- fields used by PDFs, exposed in API for parity ---
    items_total: Optional[float] = None
    total_due: Optional[float] = None
    paid_amount: Optional[float] = None
    balance: Optional[float] = None
    items: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True
