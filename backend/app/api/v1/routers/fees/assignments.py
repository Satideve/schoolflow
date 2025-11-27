# C:\coding_projects\dev\schoolflow\backend\app\api\v1\routers\fees\assignments.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.fee.fee_assignment import FeeAssignment
from app.schemas.fee.assignment import (
    FeeAssignmentCreate,
    FeeAssignmentOut,
    FeeAssignmentUpdate,
)

router = APIRouter(
    prefix="/api/v1/fee-assignments",
    tags=["fee-assignments"],
)


@router.post("/", response_model=FeeAssignmentOut, status_code=status.HTTP_201_CREATED)
def create_fee_assignment(
    payload: FeeAssignmentCreate,
    db: Session = Depends(get_db),
) -> FeeAssignment:
    obj = FeeAssignment(
        student_id=payload.student_id,
        fee_plan_id=payload.fee_plan_id,
        invoice_id=payload.invoice_id,
        concession=payload.concession,
        note=payload.note,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[FeeAssignmentOut])
def list_fee_assignments(
    student_id: Optional[int] = None,
    fee_plan_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> List[FeeAssignment]:
    query = db.query(FeeAssignment)
    if student_id is not None:
        query = query.filter(FeeAssignment.student_id == student_id)
    if fee_plan_id is not None:
        query = query.filter(FeeAssignment.fee_plan_id == fee_plan_id)
    return query.all()


@router.get("/{assignment_id}", response_model=FeeAssignmentOut)
def get_fee_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
) -> FeeAssignment:
    obj = db.get(FeeAssignment, assignment_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee assignment not found",
        )
    return obj


@router.patch("/{assignment_id}", response_model=FeeAssignmentOut)
def update_fee_assignment(
    assignment_id: int,
    payload: FeeAssignmentUpdate,
    db: Session = Depends(get_db),
) -> FeeAssignment:
    obj = db.get(FeeAssignment, assignment_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee assignment not found",
        )

    if payload.invoice_id is not None:
        obj.invoice_id = payload.invoice_id
    if payload.concession is not None:
        obj.concession = payload.concession
    if payload.note is not None:
        obj.note = payload.note

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
) -> None:
    obj = db.get(FeeAssignment, assignment_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee assignment not found",
        )
    db.delete(obj)
    db.commit()
    return None
