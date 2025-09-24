# backend/app/api/v1/routers/fees/receipts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.schemas.fee.receipt import ReceiptCreate, ReceiptOut
from app.services.fee.receipt_service import ReceiptService
from app.api.v1.dependencies import get_db, get_current_active_user
from app.models.fee.receipt import Receipt  # added for GET by id

router = APIRouter(
    prefix="/api/v1/receipts",
    tags=["fees", "receipts"],
)

@router.post("/", response_model=ReceiptOut, status_code=status.HTTP_201_CREATED)
def create_receipt(
    payload: ReceiptCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create a new receipt record, render its PDF, and return the receipt metadata.
    Idempotent: skips if a receipt for this payment_id already exists.
    """
    service = ReceiptService(db)
    existing = service.get_by_payment_id(payload.payment_id)
    if existing:
        return existing

    try:
        receipt = service.create_receipt_and_render(
            payment_id=payload.payment_id,
            receipt_no=payload.receipt_no,
        )
    except IntegrityError:
        # e.g., duplicate receipt_no
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Receipt number already in use.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return receipt


@router.get("/{receipt_id}", response_model=ReceiptOut, status_code=status.HTTP_200_OK)
def get_receipt(
    receipt_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Fetch a single receipt by its ID and return its metadata.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Receipt not found"},
        )
    return ReceiptOut.from_orm(receipt)


@router.get("/{receipt_id}/metadata", response_model=ReceiptOut, status_code=status.HTTP_200_OK)
def get_receipt_metadata(
    receipt_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Preview-only JSON metadata for a receipt (no PDF rendering or download).
    Useful for dashboards, previews, and audit logs.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Receipt not found"},
        )
    return ReceiptOut.from_orm(receipt)
