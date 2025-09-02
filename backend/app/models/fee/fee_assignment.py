# backend/app/models/fee/fee_assignment.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class FeeAssignment(Base):
    __tablename__ = "fee_assignment"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False)  # FK to student table (scaffolded)
    fee_plan_id = Column(Integer, ForeignKey("fee_plan.id"), nullable=False)
    concession = Column(Numeric(10,2), default=0)
    note = Column(String(255), nullable=True)
