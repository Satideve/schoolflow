# C:\coding_projects\dev\schoolflow\backend\app\schemas\fee\assignment.py
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel


class FeeAssignmentBase(BaseModel):
    student_id: int
    fee_plan_id: int
    invoice_id: Optional[int] = None
    concession: Decimal = Decimal("0")
    note: Optional[str] = None


class FeeAssignmentCreate(FeeAssignmentBase):
    pass


class FeeAssignmentUpdate(BaseModel):
    invoice_id: Optional[int] = None
    concession: Optional[Decimal] = None
    note: Optional[str] = None


class FeeAssignmentOut(FeeAssignmentBase):
    id: int

    class Config:
        from_attributes = True
