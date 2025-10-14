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

# Optional: plan components/models
try:
    from app.models.fee.fee_plan_component import FeePlanComponent
    from app.models.fee.fee_component import FeeComponent
except Exception:
    FeePlanComponent = None  # type: ignore
    FeeComponent = None  # type: ignore


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


def _items_from_plan_components(db: Session, plan_id: Optional[int]) -> List[Dict[str, Any]]:
    """
    If FeePlanComponent + FeeComponent exist and plan_id is provided, return a list of items.
    """
    items: List[Dict[str, Any]] = []
    if not plan_id or FeePlanComponent is None:
        return items
    try:
        comps = db.query(FeePlanComponent).filter(FeePlanComponent.fee_plan_id == plan_id).all()
        for c in comps:
            desc = None
            # try to pull human-friendly name from FeeComponent if available
            try:
                if FeeComponent is not None and getattr(c, "fee_component_id", None) is not None:
                    comp_obj = db.query(FeeComponent).filter(FeeComponent.id == c.fee_component_id).one_or_none()
                    if comp_obj:
                        desc = getattr(comp_obj, "name", None) or getattr(comp_obj, "description", None)
            except Exception:
                desc = getattr(c, "description", None)
            amount = None
            try:
                amount = float(c.amount) if getattr(c, "amount", None) is not None else None
            except Exception:
                amount = getattr(c, "amount", None)
            items.append({"id": getattr(c, "id", None), "description": desc or getattr(c, "description", None), "amount": amount})
    except Exception:
        # defensive: return empty list on any DB or attribute error
        return []
    return items


def _items_from_assignments(db: Session, invoice: FeeInvoice, student_id: Optional[int]) -> List[Dict[str, Any]]:
    """
    Attempt to build items from FeeAssignment entries that link student/plan/invoice.
    This covers cases where assignments carry item-level amounts or descriptions.
    """
    items: List[Dict[str, Any]] = []
    if FeeAssignment is None:
        return items
    try:
        q = db.query(FeeAssignment)
        # prefer invoice_id on assignment if it exists
        if hasattr(FeeAssignment, "invoice_id"):
            possible = q.filter(getattr(FeeAssignment, "invoice_id", -1) == getattr(invoice, "id", -1)).all()
        else:
            # fallback: assignments may be linked by plan_id + student_id
            plan_id = getattr(invoice, "plan_id", getattr(invoice, "fee_plan_id", None))
            if plan_id is not None and student_id is not None and hasattr(FeeAssignment, "fee_plan_id"):
                possible = q.filter(getattr(FeeAssignment, "fee_plan_id", -1) == plan_id, getattr(FeeAssignment, "student_id", None) == student_id).all()
            else:
                possible = []
        for it in possible:
            desc = getattr(it, "description", None) or getattr(it, "component_name", None) or getattr(it, "note", None)
            amount = None
            try:
                amount = float(getattr(it, "amount", None)) if getattr(it, "amount", None) is not None else None
            except Exception:
                amount = getattr(it, "amount", None)
            items.append({"id": getattr(it, "id", None), "description": desc, "amount": amount})
    except Exception:
        return []
    return items


def load_receipt_context(receipt_id: int, db: Session) -> Dict[str, Any]:
    """
    Load template context for a receipt PDF.

    Raises:
        ValueError: if the receipt with `receipt_id` is not found.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).one_or_none()
    if not receipt:
        raise ValueError(f"Receipt {receipt_id} not found")

    # Payment (optional) — try safe lookups
    payment = None
    try:
        payment = db.query(Payment).filter(Payment.id == getattr(receipt, "payment_id", None)).one_or_none()
    except Exception:
        payment = None

    # Invoice (optional, derived from payment). Support both naming conventions:
    # some code paths use `invoice_id`, others use `fee_invoice_id`.
    invoice = None
    invoice_id_candidate = None
    if payment is not None:
        invoice_id_candidate = getattr(payment, "invoice_id", None) or getattr(payment, "fee_invoice_id", None)
        if invoice_id_candidate is not None:
            try:
                invoice = db.query(FeeInvoice).filter(FeeInvoice.id == invoice_id_candidate).one_or_none()
            except Exception:
                invoice = None

    # Derive student (from invoice if present)
    student = None
    if invoice and getattr(invoice, "student_id", None) is not None:
        try:
            student = db.query(Student).filter(Student.id == invoice.student_id).one_or_none()
        except Exception:
            student = None

    # Items: prefer invoice-related items (assignments or plan components). Merge sources in preference order.
    items: List[Dict[str, Any]] = []
    if invoice:
        # 1. from FeeAssignment (if it links to invoice or student+plan)
        items = _items_from_assignments(db, invoice, getattr(invoice, "student_id", None)) or []
        # 2. if still empty, attempt to use FeePlanComponent via invoice.plan_id / invoice.fee_plan_id
        if not items:
            plan_id = getattr(invoice, "plan_id", getattr(invoice, "fee_plan_id", None))
            items = _items_from_plan_components(db, plan_id) or []

    # Student display name
    student_name = _student_display_name(student)

    # Determine amount: prefer explicit receipt.amount, then payment.amount, then invoice.amount_due
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
        "student_name": student_name,
        # items: receipts may not have line items; use invoice items if available
        "items": items,
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

    # Items building: multiple strategies, merged in preference order
    items: List[Dict[str, Any]] = []

    # 1) Try to build from FeeAssignment entries linked to this invoice or plan
    items = _items_from_assignments(db, invoice, getattr(invoice, "student_id", None)) or []

    # 2) If still empty, try FeePlanComponent -> FeeComponent via invoice.plan_id / fee_plan_id
    if not items:
        plan_id = getattr(invoice, "plan_id", getattr(invoice, "fee_plan_id", None))
        items = _items_from_plan_components(db, plan_id) or []

    # 3) As a last resort, include a single item for the whole amount_due (keeps templates sane)
    if not items:
        try:
            amt = float(invoice.amount_due) if getattr(invoice, "amount_due", None) is not None else None
        except Exception:
            amt = getattr(invoice, "amount_due", None)
        items = [{"id": None, "description": "Fees Due", "amount": amt}]

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
