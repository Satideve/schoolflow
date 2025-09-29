# backend/app/models/fee/receipt.py

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Receipt(Base):
    __tablename__ = "receipt"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payment.id"), nullable=False)
    receipt_no = Column(String(64), nullable=False, unique=True)
    pdf_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # NEW FIELD: audit trail
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)

    # relationship
    payment = relationship("Payment", back_populates="receipts")
