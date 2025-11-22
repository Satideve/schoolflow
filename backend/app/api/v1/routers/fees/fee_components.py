# C:\coding_projects\dev\schoolflow\backend\app\api\v1\routers\fees\fee_components.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.fee.fee_component import FeeComponent
from app.schemas.fee.plan import FeeComponentCreate
from app.api.dependencies.auth import get_current_user, require_roles

router = APIRouter(
    prefix="/api/v1/fee-components",
    tags=["fees"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin"))],
)
def create_fee_component(
    payload: FeeComponentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a new fee component.

    - Admin-only.
    - Name is treated as unique in practice (we can enforce at DB level if needed).
    """
    existing = db.query(FeeComponent).filter(FeeComponent.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Fee component with this name already exists",
        )

    comp = FeeComponent(
        name=payload.name,
        description=payload.description,
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


@router.get(
    "/",
)
def list_fee_components(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List all fee components.

    - Any authenticated user can read for now (admin/clerk/student/parent).
    """
    return db.query(FeeComponent).all()


@router.get(
    "/{component_id}",
)
def get_fee_component(
    component_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get a single fee component by ID.

    - Any authenticated user can read.
    """
    comp = db.query(FeeComponent).filter(FeeComponent.id == component_id).first()
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee component not found",
        )
    return comp
