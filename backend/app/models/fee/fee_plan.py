# backend/app/models/fee/fee_plan.py
from sqlalchemy import Column, Integer, String
from app.db.base import Base

class FeePlan(Base):
    __tablename__ = "fee_plan"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    academic_year = Column(String(20), nullable=False)
    frequency = Column(String(20), nullable=False)  # monthly/termly/yearly
