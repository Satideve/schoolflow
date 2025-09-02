# backend/app/models/fee/fee_invoice.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class FeeInvoice(Base):
    __tablename__ = "fee_invoice"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False)
    period = Column(String(64), nullable=False)  # e.g., "2025-04" or "Term1-2025"
    amount_due = Column(Numeric(10,2), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, paid, overdue
    created_at = Column(DateTime(timezone=True), server_default=func.now())
