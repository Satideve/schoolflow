# backend/app/models/fee/fee_assignment.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class FeeAssignment(Base):
    __tablename__ = "fee_assignment"

    id = Column(Integer, primary_key=True, index=True)
    # FK must reference the actual table name defined in Student.__tablename__ ("students")
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    fee_plan_id = Column(Integer, ForeignKey("fee_plan.id"), nullable=False)

    # optional linkage to a particular invoice (nullable to allow assignments that are not invoiced yet)
    invoice_id = Column(Integer, ForeignKey("fee_invoice.id"), nullable=True)

    concession = Column(Numeric(10, 2), default=0)
    note = Column(String(255), nullable=True)

    student = relationship("Student", back_populates="fee_assignments")
    fee_plan = relationship("FeePlan", back_populates="assignments")

    # NEW: relationship back to FeeInvoice.assignments
    invoice = relationship("FeeInvoice", back_populates="assignments")
