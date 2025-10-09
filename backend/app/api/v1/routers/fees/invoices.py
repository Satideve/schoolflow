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

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])
logger = logging.getLogger("app.audit.invoices")


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

    existing = db.query(FeeInvoice).filter(FeeInvoice.invoice_no == payload.invoice_no).first()
    if existing:
        return InvoiceOut.from_orm(existing)

    # Normalize/validate due_date robustly (accepts datetime, date, or ISO strings)
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
                try:
                    parsed_date = date.fromisoformat(due_date_val)
                    due_date = datetime.combine(parsed_date, datetime.min.time())
                except Exception:
                    raise ValueError("Invalid ISO datetime/date string")
        else:
            raise ValueError("Unsupported due_date type")
    except ValueError as ve:
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
        db.commit()  # Ensure commit after invoice creation
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

    return InvoiceOut.from_orm(inv)


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
    return [InvoiceOut.from_orm(inv) for inv in invoices]


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
    Admin/clerk see all; students see only their own.
    """
    logger.info(
        f"action=read_invoice request_id={request.state.request_id} "
        f"user_id={current_user.id} invoice_id={invoice_id}"
    )

    inv = repo_get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    if current_user.role not in ("admin", "clerk") and current_user.id != inv.student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return InvoiceOut.from_orm(inv)


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
    Stream the pre-generated PDF for a given invoice.
    Admin/clerk see all; students see only their own.
    """
    logger.info(
        f"action=download_invoice request_id={request.state.request_id} "
        f"user_id={current_user.id} invoice_id={invoice_id}"
    )

    inv = repo_get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    if current_user.role not in ("admin", "clerk") and current_user.id != inv.student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    filename = f"INV-{inv.invoice_no}.pdf"
    pdf_path = settings.invoices_path() / filename
    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice PDF not found. Please generate it first.",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
    )
