# # backend/app/models/fee/fee_plan_component.py
# from sqlalchemy import Column, Integer, ForeignKey, Numeric
# from sqlalchemy.orm import relationship
# from app.db.base import Base

# class FeePlanComponent(Base):
#     __tablename__ = "fee_plan_component"
#     id = Column(Integer, primary_key=True, index=True)
#     fee_plan_id = Column(Integer, ForeignKey("fee_plan.id"), nullable=False)
#     fee_component_id = Column(Integer, ForeignKey("fee_component.id"), nullable=False)
#     amount = Column(Numeric(10,2), nullable=False)

# backend/app/models/fee/fee_plan_component.py

from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base

class FeePlanComponent(Base):
    __tablename__ = "fee_plan_component"

    id = Column(Integer, primary_key=True, index=True)
    fee_plan_id = Column(Integer, ForeignKey("fee_plan.id"), nullable=False)
    fee_component_id = Column(Integer, ForeignKey("fee_component.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)

    # relationships
    fee_plan = relationship("FeePlan", back_populates="components")
    fee_component = relationship("FeeComponent", back_populates="plan_components")
