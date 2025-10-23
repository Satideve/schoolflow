# backend/app/models/fee/fee_invoice.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class FeeInvoice(Base):
    __tablename__ = "fee_invoice"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    invoice_no = Column(String(64), nullable=False, unique=True, index=True)
    period = Column(String(32), nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False, default=0)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # relationship back to student (if not present elsewhere)
    student = relationship("Student", back_populates="invoices")

    # NEW: relationship to FeeAssignment; matches FeeAssignment.invoice back_populates="assignments"
    assignments = relationship(
        "FeeAssignment",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    # optional convenience relationships (payments / receipts may be defined elsewhere)
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
