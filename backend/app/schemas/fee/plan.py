# backend/app/schemas/fee/plan.py
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import date

class FeePlanCreate(BaseModel):
    name: str
    academic_year: str
    frequency: str

class FeePlanOut(BaseModel):
    id: int
    name: str
    academic_year: str
    frequency: str

    class Config:
        orm_mode = True

class FeeComponentCreate(BaseModel):
    name: str
    description: Optional[str] = None

class FeePlanComponentCreate(BaseModel):
    fee_component_id: int
    amount: Decimal

class InvoiceCreate(BaseModel):
    student_id: int
    period: str
    due_date: date
