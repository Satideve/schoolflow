# backend/app/schemas/fee/plan_component.py
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FeePlanComponentBase(BaseModel):
    """Shared fields for fee plan components."""
    fee_plan_id: int
    fee_component_id: int
    amount: Decimal


class FeePlanComponentCreate(FeePlanComponentBase):
    """Payload for creating a new fee plan component."""
    pass


class FeePlanComponentUpdate(BaseModel):
    """Payload for updating an existing fee plan component."""
    fee_component_id: Optional[int] = None
    amount: Optional[Decimal] = None


class FeePlanComponent(FeePlanComponentBase):
    """Response model for a fee plan component."""
    id: int

    model_config = ConfigDict(from_attributes=True)
