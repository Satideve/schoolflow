# backend/app/api/v1/routers/fees/receipts.py

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.fee.receipt import ReceiptCreate, ReceiptOut
from app.services.fee.receipt_service import ReceiptService
from app.api.v1.dependencies import get_db
from app.api.v1.routers.auth import get_current_user
from app.models.fee.receipt import Receipt
from app.models.fee.payment import Payment
from app.models.fee.fee_invoice import FeeInvoice as Invoice
from app.core.config import settings

router = APIRouter(
    prefix="/api/v1/receipts",
    tags=["fees", "receipts"],
)

# RBAC helper:
# - Admin/Clerk: full access
# - Student/Parent: only if receipt belongs to their own student_id (via invoice linkage)
# - Others: forbidden
def _enforce_role_or_ownership(
    db: Session, current_user, receipt: Receipt
) -> None:
    """
    Enforce RBAC:
    - Admin/Clerk: full access
    - Student/Parent: only if receipt belongs to their student_id
    """
    role = getattr(current_user, "role", None)
    if role in {"admin", "clerk"}:
        return

    if role in {"student", "parent"}:
        # Ownership check via payment -> invoice -> student
        payment = db.query(Payment).filter(Payment.id == receipt.payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "Payment not found"},
            )
        invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
        if not invoice or invoice.student_id != getattr(current_user, "student_id", None):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "Not authorized to access this receipt"},
            )
        return

    # Default: deny for unknown roles
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "forbidden", "message": "Not authorized"},
    )


@router.post("/", response_model=ReceiptOut, status_code=status.HTTP_201_CREATED)
def create_receipt(
    payload: ReceiptCreate,
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),
):
    """
    Create a new receipt record, render its PDF, and return the receipt metadata.
    Idempotent: skips if a receipt for this payment_id already exists.
    Only Admin/Clerk roles can create receipts.
    """
    # Creation restricted to admin/clerk
    if getattr(current_user, "role", None) not in {"admin", "clerk"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Only admin/clerk can create receipts"},
        )

    service = ReceiptService(db)

    # Idempotency: return existing receipt if already present
    existing = service.get_by_payment_id(payload.payment_id)
    if existing:
        return existing

    try:
        # Service handles payment→invoice→student validation + rendering
        receipt = service.create_receipt_and_render(
            payment_id=payload.payment_id,
            receipt_no=payload.receipt_no,
            created_by=current_user.id,  # record who created the receipt
        )
    except IntegrityError:
        # Conflict: duplicate receipt_no
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict", "message": "Receipt number already in use."},
        )
    except Exception as exc:
        # Validation/other errors: standardized shape
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(exc)},
        )

    return receipt


@router.get("/metadata", response_model=list[ReceiptOut], status_code=status.HTTP_200_OK)
def list_receipts_metadata(
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),
):
    """
    Return metadata for all receipts.
    Useful for dashboards, admin views, and audit reports.
    - Admin/Clerk: see all
    - Student/Parent: see only their own receipts
    """
    role = getattr(current_user, "role", None)
    # Order by most recent first for dashboard friendliness
    query = db.query(Receipt).order_by(Receipt.created_at.desc())

    if role in {"admin", "clerk"}:
        receipts = query.all()
    elif role in {"student", "parent"}:
        # Scope to current user's student_id via joins
        receipts = (
            query.join(Payment, Receipt.payment_id == Payment.id)
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .filter(Invoice.student_id == getattr(current_user, "student_id", None))
            .all()
        )
    else:
        # Unknown/unsupported role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Not authorized"},
        )

    return [ReceiptOut.from_orm(r) for r in receipts]


@router.get("/{receipt_id}/metadata", response_model=ReceiptOut, status_code=status.HTTP_200_OK)
def get_receipt_metadata(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),
):
    """
    Preview-only JSON metadata for a single receipt.
    """
    # Fetch target receipt
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Receipt not found"},
        )

    # Enforce RBAC/ownership
    _enforce_role_or_ownership(db, current_user, receipt)
    return ReceiptOut.from_orm(receipt)


@router.get("/{receipt_id}", response_model=ReceiptOut, status_code=status.HTTP_200_OK)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),
):
    """
    Fetch a single receipt by its ID and return its metadata.
    """
    # Fetch target receipt
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Receipt not found"},
        )

    # Enforce RBAC/ownership
    _enforce_role_or_ownership(db, current_user, receipt)
    return ReceiptOut.from_orm(receipt)


def _backend_root() -> str:
    """
    Resolve the backend directory (…/backend) robustly from this file path.
    """
    p = Path(__file__).resolve()
    # Path: backend/app/api/v1/routers/fees/receipts.py
    # parents: [fees, routers, v1, api, app, backend, <repo root>]
    backend_dir = p.parents[4]  # index 4 -> backend
    return str(backend_dir)


def _resolve_pdf_path(pdf_path: str) -> str:
    """
    Normalize stored receipt pdf_path (e.g., 'app/data/receipts/RCT-...pdf')
    to an absolute path inside the container. Join with backend root.
    Keep the leading 'app/' because PDFs are under backend/app/data/receipts.
    """
    base_dir = getattr(settings, "base_dir", None) or _backend_root()
    rel = pdf_path.replace("\\", "/")
    rel = rel.lstrip("/")  # avoid accidental absolute join issues

    # First attempt: backend + pdf_path (keeps 'app/')
    candidate = os.path.join(base_dir, rel)
    if os.path.isfile(candidate):
        return candidate

    # Second attempt: if base_dir already includes 'app', try without 'app/'
    if rel.startswith("app/"):
        alt = os.path.join(base_dir, rel[4:])
        if os.path.isfile(alt):
            return alt

    # Return the first candidate (for error reporting)
    return candidate


@router.get("/{receipt_id}/download", response_class=FileResponse)
def download_receipt_pdf(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),
):
    """
    Stream the PDF file for a given receipt_id.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Receipt not found"},
        )

    _enforce_role_or_ownership(db, current_user, receipt)

    file_path = _resolve_pdf_path(receipt.pdf_path)
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"PDF file missing on server: {file_path}"},
        )

    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
    )
