# backend/app/api/v1/routers/fees/plans.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.fee.plan import FeePlanCreate, FeePlanOut
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.fee_repo import create_fee_plan, get_fee_plan

router = APIRouter(prefix="/api/v1/fee-plans", tags=["fees"])

@router.post("/", response_model=FeePlanOut)
def create_plan(payload: FeePlanCreate, db: Session = Depends(get_db)):
    plan = create_fee_plan(db, name=payload.name, academic_year=payload.academic_year, frequency=payload.frequency)
    return plan

@router.get("/{plan_id}", response_model=FeePlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = get_fee_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"Fee plan not found"})
    return plan
