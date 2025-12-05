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
from app.schemas.fee.invoice import InvoiceCreate, InvoiceOut
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

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])
logger = logging.getLogger("app.audit.invoices")


def _invoice_out_with_context(inv: FeeInvoice, db: Session) -> InvoiceOut:
    """
    Build InvoiceOut from ORM + merge PDF context values for parity with rendered PDFs.
    Non-invasive: if keys are missing in context, we leave them as None.
    """
    base = InvoiceOut.from_orm(inv)
    try:
        ctx = load_invoice_context(inv.id, db)
        merged = base.model_dump()
        for k in ("items_total", "total_due", "paid_amount", "balance", "items"):
            if k in ctx:
                merged[k] = ctx.get(k)
        return InvoiceOut(**merged)
    except Exception:
        return base


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
