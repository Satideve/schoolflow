# backend/app/services/pdf/context_loader.py

"""
Context loader utilities for invoice and receipt PDF rendering.

This module exposes two functions used by the PDF renderer:
- load_receipt_context(receipt_id, db)  -> dict
- load_invoice_context(invoice_id, db)  -> dict

They return a plain dict of template variables expected by the Jinja templates
used for receipts/invoices. The functions are defensive: they only raise a
ValueError when the requested primary entity (receipt or invoice) is missing.
They try to populate common fields that the templates consume so invoice
rendering (which reuses the receipt renderer) does not fail when a given
field is absent.

This file replaces the previous implementation which accidentally raised
`Receipt <id> not found` during invoice rendering. The new implementation
ensures `load_invoice_context` looks up invoices (not receipts) and also
provides any related `payment` objects so invoice templates that expect
a `payment` variable won't error.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

# Import domain models (local imports keep things explicit)
from app.models.fee.receipt import Receipt
from app.models.fee.fee_invoice import FeeInvoice
from app.models.fee.payment import Payment
from app.models.student import Student

# Optional: fee assignment / line items (if present)
try:
    from app.models.fee.fee_assignment import FeeAssignment  # may or may not be used
except Exception:
    FeeAssignment = None  # type: ignore


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def _student_display_name(student: Optional[Student]) -> Optional[str]:
    if not student:
        return None
    # try common fields used across apps
    for attr in ("name", "full_name", "display_name"):
        val = getattr(student, attr, None)
        if val:
            return val
    # fallback to email or id
    return getattr(student, "email", None) or (str(student.id) if getattr(student, "id", None) else None)


def load_receipt_context(receipt_id: int, db: Session) -> Dict[str, Any]:
    """
    Load template context for a receipt PDF.

    Raises:
        ValueError: if the receipt with `receipt_id` is not found.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).one_or_none()
    if not receipt:
        raise ValueError(f"Receipt {receipt_id} not found")

    # Payment (optional)
    payment = None
    try:
        payment = db.query(Payment).filter(Payment.id == getattr(receipt, "payment_id", None)).one_or_none()
    except Exception:
        payment = None

    # Invoice (optional, derived from payment.invoice_id if present)
    invoice = None
    if payment and getattr(payment, "invoice_id", None) is not None:
        try:
            invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payment.invoice_id).one_or_none()
        except Exception:
            invoice = None

    # Student (optional, derived from invoice.student_id)
    student = None
    if invoice and getattr(invoice, "student_id", None) is not None:
        try:
            student = db.query(Student).filter(Student.id == invoice.student_id).one_or_none()
        except Exception:
            student = None

    # Build a safe context with reasonable defaults
    amount = None
    if getattr(receipt, "amount", None) is not None:
        try:
            amount = float(receipt.amount)
        except Exception:
            amount = receipt.amount
    elif payment and getattr(payment, "amount", None) is not None:
        try:
            amount = float(payment.amount)
        except Exception:
            amount = payment.amount
    elif invoice and getattr(invoice, "amount_due", None) is not None:
        try:
            amount = float(invoice.amount_due)
        except Exception:
            amount = invoice.amount_due

    ctx: Dict[str, Any] = {
        "receipt_id": getattr(receipt, "id", None),
        "receipt_no": getattr(receipt, "receipt_no", None),
        "amount": amount,
        "issued_date": _iso(getattr(receipt, "issued_date", getattr(receipt, "created_at", None))),
        "payment": payment,
        "invoice": invoice,
        "invoice_no": getattr(invoice, "invoice_no", None) if invoice else None,
        "student": student,
        "student_name": _student_display_name(student),
        # items: receipts may not have line items; leave empty list if none
        "items": [],
        # raw objects kept for template authors who prefer object attributes
        "_raw": {"receipt": receipt, "payment": payment, "invoice": invoice, "student": student},
    }

    return ctx


def load_invoice_context(invoice_id: int, db: Session) -> Dict[str, Any]:
    """
    Load template context for an invoice PDF.

    Raises:
        ValueError: if the invoice with `invoice_id` is not found.
    """
    invoice = db.query(FeeInvoice).filter(FeeInvoice.id == invoice_id).one_or_none()
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")

    # Student (optional)
    student = None
    if getattr(invoice, "student_id", None) is not None:
        try:
            student = db.query(Student).filter(Student.id == invoice.student_id).one_or_none()
        except Exception:
            student = None

    # Try to build line items from FeeAssignment if available and linked to invoice/plan
    items: List[Dict[str, Any]] = []
    if FeeAssignment is not None:
        try:
            # FeeAssignment may reference invoice_id or plan_id depending on schema.
            # We'll attempt both safe queries without causing an exception.
            possible_items = db.query(FeeAssignment).filter(getattr(FeeAssignment, "invoice_id", -1) == invoice_id).all()
            if not possible_items:
                # fallback: assignments linked by plan_id or other logic (best-effort)
                possible_items = db.query(FeeAssignment).filter(getattr(FeeAssignment, "plan_id", -1) == getattr(invoice, "plan_id", -1)).all()
            for it in possible_items:
                items.append(
                    {
                        "id": getattr(it, "id", None),
                        "description": getattr(it, "description", None) or getattr(it, "component_name", None),
                        "amount": float(getattr(it, "amount", 0)) if getattr(it, "amount", None) is not None else None,
                    }
                )
        except Exception:
            items = []

    # Ensure amount fields are available in a template-friendly way
    amount_due = None
    if getattr(invoice, "amount_due", None) is not None:
        try:
            amount_due = float(invoice.amount_due)
        except Exception:
            amount_due = invoice.amount_due

    # Payments: include recent payments linked to this invoice so invoice templates
    # that expect `payment` or `payments` won't fail. We prefer the most recent payment.
    payments: List[Payment] = []
    payment: Optional[Payment] = None
    try:
        payments = (
            db.query(Payment)
            .filter(Payment.fee_invoice_id == invoice_id)
            .order_by(getattr(Payment, "created_at", None).desc() if getattr(Payment, "created_at", None) is not None else Payment.id.desc())
            .all()
        )
        if payments:
            payment = payments[0]
    except Exception:
        payments = []
        payment = None

    ctx: Dict[str, Any] = {
        "invoice_id": getattr(invoice, "id", None),
        "invoice_no": getattr(invoice, "invoice_no", None),
        "invoice": invoice,  # <-- ensure templates referencing `invoice` find it
        "period": getattr(invoice, "period", None),
        "amount_due": amount_due,
        "due_date": _iso(getattr(invoice, "due_date", None)),
        "student": student,
        "student_name": _student_display_name(student),
        "items": items,
        # Keep raw invoice object available for templates needing it
        "_raw": {"invoice": invoice, "student": student, "payment": payment, "payments": payments},
        # Also include some aliases that templates using receipt layout might expect:
        "amount": amount_due,
        "issued_date": _iso(getattr(invoice, "created_at", None) or getattr(invoice, "issued_date", None)),
        # Include payment(s) so templates that reference `payment` won't raise
        "payment": payment,
        "payments": payments,
    }

    return ctx
