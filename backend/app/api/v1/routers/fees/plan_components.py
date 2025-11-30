# backend/app/api/v1/routers/fees/plan_components.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.fee.fee_plan_component import FeePlanComponent as FeePlanComponentModel
from app.schemas.fee.plan_component import (
    FeePlanComponentCreate,
    FeePlanComponentUpdate,
    FeePlanComponent as FeePlanComponentSchema,
)

router = APIRouter(
    prefix="/api/v1/fee-plan-components",
    tags=["fee-plan-components"],
)


@router.post(
    "/",
    response_model=FeePlanComponentSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_fee_plan_component(
    payload: FeePlanComponentCreate,
    db: Session = Depends(get_db),
) -> FeePlanComponentModel:
    obj = FeePlanComponentModel(
        fee_plan_id=payload.fee_plan_id,
        fee_component_id=payload.fee_component_id,
        amount=payload.amount,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[FeePlanComponentSchema])
def list_fee_plan_components(
    fee_plan_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[FeePlanComponentModel]:
    query = db.query(FeePlanComponentModel)
    if fee_plan_id is not None:
        query = query.filter(FeePlanComponentModel.fee_plan_id == fee_plan_id)
    return query.all()


@router.get("/{component_id}", response_model=FeePlanComponentSchema)
def get_fee_plan_component(
    component_id: int,
    db: Session = Depends(get_db),
) -> FeePlanComponentModel:
    obj = db.get(FeePlanComponentModel, component_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee plan component not found",
        )
    return obj


@router.patch("/{component_id}", response_model=FeePlanComponentSchema)
def update_fee_plan_component(
    component_id: int,
    payload: FeePlanComponentUpdate,
    db: Session = Depends(get_db),
) -> FeePlanComponentModel:
    obj = db.get(FeePlanComponentModel, component_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee plan component not found",
        )

    if payload.fee_component_id is not None:
        obj.fee_component_id = payload.fee_component_id
    if payload.amount is not None:
        obj.amount = payload.amount

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee_plan_component(
    component_id: int,
    db: Session = Depends(get_db),
) -> None:
    obj = db.get(FeePlanComponentModel, component_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee plan component not found",
        )
    db.delete(obj)
    db.commit()
    return None
