# backend/app/api/v1/routers/fees/invoices.py

import logging
from pathlib import Path
from datetime import datetime, date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.fee.fee_invoice import FeeInvoice
from app.models.user import User
from app.models.student import Student
from app.schemas.fee.invoice import (
    InvoiceCreate,
    InvoiceOut,
    InvoiceItemCreate,
)

from app.services.fee.fees_service import FeesService
from app.services.payments.fake_adapter import FakePaymentAdapter
from app.services.messaging.fake_adapter import FakeMessagingAdapter
from app.repositories.invoice_repo import (
    get_invoice as repo_get_invoice,
    list_invoices as repo_list_invoices,
)
from app.core.config import settings
from app.api.dependencies.auth import get_current_user, require_roles

# Use context loader to compute items_total / total_due / paid_amount / balance / items
from app.services.pdf.context_loader import load_invoice_context
# Renderer for PDFs
from app.services.pdf.renderer import render_invoice_pdf

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from app.models.fee.fee_invoice_item import FeeInvoiceItem

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])
logger = logging.getLogger("app.audit.invoices")



def _invoice_out_with_context(inv: FeeInvoice, db: Session) -> InvoiceOut:
    """
    Build InvoiceOut from ORM + merge PDF context values for parity with rendered PDFs.

    IMPORTANT:
    - We avoid Pydantic's from_orm here because it tries to lazy-load relationships
      (e.g. FeeInvoice.items), which can cause DetachedInstanceError when the
      instance is not bound to a live Session.
    - Instead we construct the base payload manually from scalar fields only,
      then merge in context-derived fields (items_total, total_due, etc.).
    """
    base = InvoiceOut(
        id=inv.id,
        student_id=inv.student_id,
        invoice_no=inv.invoice_no,
        period=getattr(inv, "period", None),
        due_date=getattr(inv, "due_date", None),
        amount_due=getattr(inv, "amount_due", None),
        payment=None,  # not stored on the ORM; only used as input
        status=getattr(inv, "status", "pending"),
        created_at=getattr(inv, "created_at", None),
        items_total=None,
        total_due=None,
        paid_amount=None,
        balance=None,
        items=None,
    )

    try:
        ctx = load_invoice_context(inv.id, db)
        merged = base.model_dump()
        for k in ("items_total", "total_due", "paid_amount", "balance", "items"):
            if k in ctx:
                merged[k] = ctx.get(k)
        return InvoiceOut(**merged)
    except Exception:
        # If context loading fails for any reason, fall back to base fields only.
        return base

# ---- Invoice item DTOs & helpers (admin line items) -------------------------


class InvoiceItemOut(BaseModel):
    id: int
    description: str
    amount: Decimal

    class Config:
        from_attributes = True


class InvoiceItemUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None


def _to_decimal(v) -> Decimal:
    """Safe Decimal conversion for numeric DB values."""
    if v is None:
        return Decimal("0")
    try:
        return Decimal(v)  # already Decimal / numeric
    except Exception:
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")



@router.post(
    "/",
    response_model=InvoiceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "clerk"))],
)
def create_invoice(
    payload: InvoiceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new invoice record.
    Only admin or clerk can create.
    Idempotent: returns existing invoice if invoice_no already exists.
    """
    logger.info(
        f"action=create_invoice request_id={request.state.request_id} "
        f"user_id={current_user.id} student_id={payload.student_id} invoice_no={payload.invoice_no}"
    )

    # Ensure target student exists
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with id {payload.student_id} not found",
        )

    existing = db.query(FeeInvoice).filter(FeeInvoice.invoice_no == payload.invoice_no).first()
    if existing:
        return _invoice_out_with_context(existing, db)

    # Normalize/validate due_date (accept datetime/date/ISO str)
    due_date_val = payload.due_date
    try:
        if isinstance(due_date_val, datetime):
            due_date = due_date_val
        elif isinstance(due_date_val, date):
            due_date = datetime.combine(due_date_val, datetime.min.time())
        elif isinstance(due_date_val, str):
            try:
                due_date = datetime.fromisoformat(due_date_val)
            except Exception:
                parsed_date = date.fromisoformat(due_date_val)
                due_date = datetime.combine(parsed_date, datetime.min.time())
        else:
            raise ValueError("Unsupported due_date type")
    except Exception as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid due_date: {ve}")

    svc = FeesService(
        db=db,
        payment_gateway=FakePaymentAdapter(),
        messaging=FakeMessagingAdapter(),
    )

    try:
        inv = svc.generate_invoice_for_student(
            student_id=payload.student_id,
            invoice_no=payload.invoice_no,
            period=payload.period,
            amount=payload.amount_due,
            due_date=due_date,
            payment=payload.payment,
            line_items=[li.model_dump() for li in (payload.line_items or [])],
            base_amount_description=payload.base_amount_description, 
        )
        db.commit()
        db.refresh(inv)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoice number already exists.",
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return _invoice_out_with_context(inv, db)


@router.get(
    "/",
    response_model=List[InvoiceOut],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("admin", "clerk"))],
)
def list_invoices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return list of all invoices.
    Only admin or clerk can list.
    """
    logger.info(
        f"action=list_invoices request_id={request.state.request_id} user_id={current_user.id}"
    )
    invoices = repo_list_invoices(db)
    return [_invoice_out_with_context(inv, db) for inv in invoices]


@router.get(
    "/mine",
    response_model=List[InvoiceOut],
    status_code=status.HTTP_200_OK,
)
def list_my_invoices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return invoices visible to the current user.

    - Admin / clerk: all invoices (same as list_invoices).
    - Student / parent: only invoices whose student_id matches current_user.student_id.
    - Others: empty list for now.
    """
    logger.info(
        f"action=list_my_invoices request_id={request.state.request_id} "
        f"user_id={current_user.id} role={current_user.role} student_id={getattr(current_user, 'student_id', None)}"
    )

    if current_user.role in ("admin", "clerk"):
        invoices = repo_list_invoices(db)
    elif current_user.role in ("student", "parent"):
        if current_user.student_id is None:
            invoices = []
        else:
            invoices = (
                db.query(FeeInvoice)
                .filter(FeeInvoice.student_id == current_user.student_id)
                .all()
            )
    else:
        invoices = []

    return [_invoice_out_with_context(inv, db) for inv in invoices]


@router.get(
    "/{invoice_id}",
    response_model=InvoiceOut,
    status_code=status.HTTP_200_OK,
)
def read_invoice(
    invoice_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a single invoice by its ID.
    Admin/clerk see all; students see only their own (via student_id mapping).
    """
    logger.info(
        f"action=read_invoice request_id={request.state.request_id} "
        f"user_id={current_user.id} invoice_id={invoice_id} student_id={getattr(current_user, 'student_id', None)}"
    )

    inv = repo_get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    if current_user.role not in ("admin", "clerk"):
        # Student/parent/etc must match by student_id
        if current_user.student_id is None or current_user.student_id != inv.student_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return _invoice_out_with_context(inv, db)


@router.get(
    "/{invoice_id}/download",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download the invoice PDF",
)
def download_invoice(
    invoice_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stream the (re-)rendered PDF for a given invoice.

    RBAC:
    - Admin/clerk see all.
    - Students/parents: only invoices whose student_id matches their mapped student_id.

    IMPORTANT:
    - We ALWAYS attempt to render a fresh PDF using the current invoice context
      (items, totals, payments, balance).
    - If rendering fails but an existing PDF file is present, we fall back to that file.
    - If rendering fails and no file exists, we raise 500.
    """
    logger.info(
        f"action=download_invoice request_id={request.state.request_id} "
        f"user_id={current_user.id} invoice_id={invoice_id} student_id={getattr(current_user, 'student_id', None)}"
    )

    inv = repo_get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    # RBAC check
    if current_user.role not in ("admin", "clerk"):
        if current_user.student_id is None or current_user.student_id != inv.student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

    filename = f"INV-{inv.invoice_no}.pdf"
    pdf_path = settings.invoices_path() / filename

    # Try to (re-)render the latest PDF based on current context
    render_error: Exception | None = None
    try:
        ctx = load_invoice_context(inv.id, db)
        Path(pdf_path.parent).mkdir(parents=True, exist_ok=True)
        render_invoice_pdf(ctx, str(pdf_path))
        logger.info(
            "Rendered (or updated) invoice PDF at %s for invoice %s (id=%s)",
            str(pdf_path),
            inv.invoice_no,
            inv.id,
        )
    except Exception as e:
        render_error = e
        logger.exception(
            "Failed to render invoice PDF for invoice %s (id=%s): %s",
            inv.invoice_no,
            inv.id,
            e,
        )

    # If we couldn't render AND the file doesn't exist, treat as server error
    if render_error is not None and not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to render invoice PDF: {render_error}",
        )

    # At this point, either we have a freshly rendered file, or we fall back to an existing one.
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
    )

# ---------------------------------------------------------------------------
#                ADMIN: INVOICE LINE-ITEM CRUD (fee_invoice_item)
# ---------------------------------------------------------------------------

@router.get(
    "/{invoice_id}/items",
    response_model=List[InvoiceItemOut],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("admin", "clerk"))],
)
def list_invoice_items(
    invoice_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List manual line items for a given invoice (fee_invoice_item rows).
    Only admin / clerk.
    """
    inv = repo_get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    items = (
        db.query(FeeInvoiceItem)
        .filter(FeeInvoiceItem.fee_invoice_id == invoice_id)
        .order_by(FeeInvoiceItem.id.asc())
        .all()
    )
    return items


@router.post(
    "/{invoice_id}/items",
    response_model=InvoiceItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "clerk"))],
)
def create_invoice_item(
    invoice_id: int,
    payload: InvoiceItemCreate,  # from app.schemas.fee.invoice
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a new manual line item to an invoice and bump amount_due by item amount.
    """
    inv = repo_get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    item = FeeInvoiceItem(
        fee_invoice_id=invoice_id,
        description=payload.description,
        amount=payload.amount,
    )
    db.add(item)

    # Adjust invoice.amount_due by the item amount
    current_due = _to_decimal(inv.amount_due)
    inv.amount_due = current_due + _to_decimal(payload.amount)

    db.commit()
    db.refresh(item)
    db.refresh(inv)
    return item


@router.patch(
    "/{invoice_id}/items/{item_id}",
    response_model=InvoiceItemOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("admin", "clerk"))],
)
def update_invoice_item(
    invoice_id: int,
    item_id: int,
    payload: InvoiceItemUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing manual line item (description/amount) and adjust amount_due by delta.
    """
    inv = repo_get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    item = (
        db.query(FeeInvoiceItem)
        .filter(
            FeeInvoiceItem.id == item_id,
            FeeInvoiceItem.fee_invoice_id == invoice_id,
        )
        .one_or_none()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found",
        )

    # Track old amount for delta
    old_amount = _to_decimal(item.amount)
    new_amount = old_amount

    if payload.description is not None:
        item.description = payload.description

    if payload.amount is not None:
        new_amount = _to_decimal(payload.amount)
        item.amount = new_amount

    # Adjust invoice.amount_due by delta (new - old)
    delta = new_amount - old_amount
    if delta != 0:
        inv.amount_due = _to_decimal(inv.amount_due) + delta

    db.commit()
    db.refresh(item)
    db.refresh(inv)
    return item


@router.delete(
    "/{invoice_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin", "clerk"))],
)
def delete_invoice_item(
    invoice_id: int,
    item_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a manual line item and reduce invoice.amount_due by that amount.
    """
    inv = repo_get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    item = (
        db.query(FeeInvoiceItem)
        .filter(
            FeeInvoiceItem.id == item_id,
            FeeInvoiceItem.fee_invoice_id == invoice_id,
        )
        .one_or_none()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found",
        )

    old_amount = _to_decimal(item.amount)

    # Reduce amount_due by the item amount
    inv.amount_due = _to_decimal(inv.amount_due) - old_amount

    db.delete(item)
    db.commit()
    # 204: no content
    return None
