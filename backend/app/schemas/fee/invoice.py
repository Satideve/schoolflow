# backend/app/schemas/fee/invoice.py

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any


class InvoiceItemCreate(BaseModel):
    """
    Single line item for an invoice, entered by admin.
    Used *inside* InvoiceCreate (no invoice_id here).
    """
    description: str
    amount: Decimal


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

    # NEW: admin-entered line items for this invoice
    line_items: List[InvoiceItemCreate] = []


class InvoiceOut(InvoiceCreate):
    id: int
    status: str
    created_at: datetime

    # --- fields used by PDFs, exposed in API for parity ---
    items_total: Optional[float] = None
    total_due: Optional[float] = None
    paid_amount: Optional[float] = None
    balance: Optional[float] = None
    items: Optional[List[Any]] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------
# Extra schemas for dedicated fee_invoice_item CRUD (Step 28)
# These do NOT change existing behaviour; they are additional types
# we can use in a new router later.
# ------------------------------------------------------------------


class FeeInvoiceItemBase(BaseModel):
    """Shared fields for an invoice line item tied to a specific invoice."""
    fee_invoice_id: int
    description: str
    amount: Decimal


class FeeInvoiceItemCreate(FeeInvoiceItemBase):
    """Payload for creating a new invoice line item."""
    pass


class FeeInvoiceItemUpdate(BaseModel):
    """Payload for updating an existing invoice line item."""
    description: Optional[str] = None
    amount: Optional[Decimal] = None


class FeeInvoiceItemOut(FeeInvoiceItemBase):
    """Response model for an invoice line item."""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
