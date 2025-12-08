# backend/app/api/v1/routers/fees/invoice_items.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.dependencies.auth import get_current_user, require_roles
from app.models.user import User
from app.models.fee.fee_invoice import FeeInvoice
from app.models.fee.fee_invoice_item import FeeInvoiceItem
from app.schemas.fee.invoice import (
    FeeInvoiceItemCreate,
    FeeInvoiceItemUpdate,
    FeeInvoiceItemOut,
)

router = APIRouter(
    prefix="/api/v1/invoice-items",
    tags=["invoice-items"],
    dependencies=[Depends(require_roles("admin", "clerk"))],
)


@router.get(
    "/by-invoice/{invoice_id}",
    response_model=List[FeeInvoiceItemOut],
    status_code=status.HTTP_200_OK,
)
def list_invoice_items(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all line items for a given invoice.
    Admin / clerk only (enforced by dependency).
    """
    invoice = db.query(FeeInvoice).filter(FeeInvoice.id == invoice_id).first()
    if not invoice:
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
    "/",
    response_model=FeeInvoiceItemOut,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice_item(
    payload: FeeInvoiceItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new line item for an invoice.

    NOTE:
    - This does *not* automatically change invoice.amount_due.
      The invoice total is still derived via load_invoice_context and
      used when rendering PDFs and computing balances.
    """
    invoice = (
        db.query(FeeInvoice)
        .filter(FeeInvoice.id == payload.fee_invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    item = FeeInvoiceItem(
        fee_invoice_id=payload.fee_invoice_id,
        description=payload.description,
        amount=payload.amount,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch(
    "/{item_id}",
    response_model=FeeInvoiceItemOut,
    status_code=status.HTTP_200_OK,
)
def update_invoice_item(
    item_id: int,
    payload: FeeInvoiceItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing invoice line item.

    Only description and amount are editable.
    """
    item = db.query(FeeInvoiceItem).filter(FeeInvoiceItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found",
        )

    if payload.description is not None:
        item.description = payload.description
    if payload.amount is not None:
        item.amount = payload.amount

    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_invoice_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an invoice line item.
    """
    item = db.query(FeeInvoiceItem).filter(FeeInvoiceItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found",
        )

    db.delete(item)
    db.commit()
    return None
