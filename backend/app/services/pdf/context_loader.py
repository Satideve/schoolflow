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

# Optional fee-plan component models (used as fallback line-items)
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


def _safe_float(v):
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        try:
            return float(str(v))
        except Exception:
            return None


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

    # Invoice (optional, derived from payment.fee_invoice_id if present)
    invoice = None
    if payment and getattr(payment, "fee_invoice_id", None) is not None:
        try:
            invoice = db.query(FeeInvoice).filter(FeeInvoice.id == payment.fee_invoice_id).one_or_none()
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
    # amount: priority -> receipt.amount -> payment.amount -> invoice.amount_due
    amount = None
    if getattr(receipt, "amount", None) is not None:
        amount = _safe_float(getattr(receipt, "amount"))
    elif payment and getattr(payment, "amount", None) is not None:
        amount = _safe_float(getattr(payment, "amount"))
    elif invoice and getattr(invoice, "amount_due", None) is not None:
        amount = _safe_float(getattr(invoice, "amount_due"))

    # Attempt to build items from invoice -> fallback to assignment -> plan components
    items: List[Dict[str, Any]] = []

    # If invoice exists, try to gather items via invoice-related data (reuse load_invoice logic lightly)
    try:
        if invoice:
            # look for FeeAssignment rows related to invoice or student which may act as line items
            if FeeAssignment is not None:
                possible_items = db.query(FeeAssignment).filter(getattr(FeeAssignment, "invoice_id", -1) == getattr(invoice, "id", -1)).all()
                if not possible_items:
                    # fallback: assignments linked by student & plan
                    possible_items = db.query(FeeAssignment).filter(getattr(FeeAssignment, "student_id", -1) == getattr(invoice, "student_id", -1)).all()
                for it in possible_items:
                    items.append(
                        {
                            "id": getattr(it, "id", None),
                            "description": getattr(it, "description", None) or getattr(it, "component_name", None) or None,
                            "amount": _safe_float(getattr(it, "amount", None)),
                        }
                    )
    except Exception:
        items = []

    # If still empty, attempt to derive from student's assigned fee plan components
    if not items and FeeAssignment is not None and FeePlanComponent is not None:
        try:
            # try get assignment for student
            assignment = None
            if student:
                assignment = db.query(FeeAssignment).filter(getattr(FeeAssignment, "student_id", -1) == getattr(student, "id", -1)).first()
            if assignment and getattr(assignment, "fee_plan_id", None):
                components = db.query(FeePlanComponent).filter(getattr(FeePlanComponent, "fee_plan_id") == getattr(assignment, "fee_plan_id")).all()
                for comp in components:
                    # try to get a human-friendly name from FeeComponent if available
                    comp_name = None
                    try:
                        if FeeComponent is not None and getattr(comp, "fee_component_id", None) is not None:
                            cobj = db.query(FeeComponent).filter(getattr(FeeComponent, "id") == getattr(comp, "fee_component_id")).one_or_none()
                            if cobj:
                                comp_name = getattr(cobj, "name", None)
                    except Exception:
                        comp_name = None
                    items.append(
                        {
                            "id": getattr(comp, "id", None),
                            "description": comp_name or getattr(comp, "description", None) or getattr(comp, "name", None),
                            "amount": _safe_float(getattr(comp, "amount", None)),
                        }
                    )
        except Exception:
            # ignore; items remain as found
            pass

    # payments: collect recent payments that relate to this receipt/invoice
    payments: List[Payment] = []
    try:
        if payment:
            # include the payment used by this receipt
            payments = [payment]
        elif invoice:
            payments = db.query(Payment).filter(Payment.fee_invoice_id == invoice.id).order_by(getattr(Payment, "created_at", None).desc() if getattr(Payment, "created_at", None) is not None else Payment.id.desc()).all()
    except Exception:
        payments = []

    # compute paid_amount (sum of payments)
    paid_amount = None
    try:
        if payments:
            s = 0.0
            for p in payments:
                a = _safe_float(getattr(p, "amount", None))
                if a is not None:
                    s += a
            paid_amount = s
    except Exception:
        paid_amount = None

    ctx: Dict[str, Any] = {
        # primary fields
        "receipt_id": getattr(receipt, "id", None),
        "receipt_no": getattr(receipt, "receipt_no", None),
        "amount": amount,
        "paid_amount": paid_amount,
        "issued_date": _iso(getattr(receipt, "issued_date", getattr(receipt, "created_at", None))),
        "payment": payment,
        "invoice": invoice,
        "invoice_no": getattr(invoice, "invoice_no", None) if invoice else None,
        "student": student,
        "student_name": _student_display_name(student),
        # items and raw objects
        "items": items,
        "_raw": {"receipt": receipt, "payment": payment, "invoice": invoice, "student": student},
        "payments": payments,
        # aliases & convenience fields for templates
        "total": amount,
        "fees_due": amount,
        # document metadata helpers
        "document_type": "receipt",
        "title": "Receipt",
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
            # FeeAssignment may reference invoice_id or student_id depending on schema.
            possible_items = db.query(FeeAssignment).filter(getattr(FeeAssignment, "invoice_id", -1) == invoice_id).all()
            if not possible_items:
                possible_items = db.query(FeeAssignment).filter(getattr(FeeAssignment, "student_id", -1) == getattr(invoice, "student_id", -1)).all()
            for it in possible_items:
                items.append(
                    {
                        "id": getattr(it, "id", None),
                        "description": getattr(it, "description", None) or getattr(it, "component_name", None),
                        "amount": _safe_float(getattr(it, "amount", None)),
                    }
                )
        except Exception:
            items = []

    # If items empty, attempt to use fee_plan components (if the student has an assignment with fee_plan)
    if not items and FeeAssignment is not None and FeePlanComponent is not None:
        try:
            assignment = None
            if student:
                assignment = db.query(FeeAssignment).filter(getattr(FeeAssignment, "student_id", -1) == getattr(student, "id", -1)).first()
            if assignment and getattr(assignment, "fee_plan_id", None):
                components = db.query(FeePlanComponent).filter(getattr(FeePlanComponent, "fee_plan_id") == getattr(assignment, "fee_plan_id")).all()
                for comp in components:
                    comp_name = None
                    try:
                        if FeeComponent is not None and getattr(comp, "fee_component_id", None) is not None:
                            cobj = db.query(FeeComponent).filter(getattr(FeeComponent, "id") == getattr(comp, "fee_component_id")).one_or_none()
                            if cobj:
                                comp_name = getattr(cobj, "name", None)
                    except Exception:
                        comp_name = None
                    items.append(
                        {
                            "id": getattr(comp, "id", None),
                            "description": comp_name or getattr(comp, "description", None) or getattr(comp, "name", None),
                            "amount": _safe_float(getattr(comp, "amount", None)),
                        }
                    )
        except Exception:
            pass

    # Ensure amount fields are available in a template-friendly way
    amount_due = _safe_float(getattr(invoice, "amount_due", None))

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

    # Sum paid amount
    paid_amount = None
    try:
        if payments:
            s = 0.0
            for p in payments:
                a = _safe_float(getattr(p, "amount", None))
                if a is not None:
                    s += a
            paid_amount = s
    except Exception:
        paid_amount = None

    ctx: Dict[str, Any] = {
        # primary invoice fields
        "invoice_id": getattr(invoice, "id", None),
        "invoice_no": getattr(invoice, "invoice_no", None),
        "invoice": invoice,  # ensure templates referencing `invoice` find it
        "period": getattr(invoice, "period", None),
        "amount_due": amount_due,
        "due_date": _iso(getattr(invoice, "due_date", None)),
        "student": student,
        "student_name": _student_display_name(student),
        "items": items,
        # raw objects and payments
        "_raw": {"invoice": invoice, "student": student, "payment": payment, "payments": payments},
        "payment": payment,
        "payments": payments,
        # aliases used by templates
        "amount": amount_due,
        "total": amount_due,
        "fees_due": amount_due,
        "paid_amount": paid_amount,
        "issued_date": _iso(getattr(invoice, "created_at", None) or getattr(invoice, "issued_date", None)),
        # document metadata helpers
        "document_type": "invoice",
        "title": "Invoice",
    }

    return ctx

