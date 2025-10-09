# backend/app/models/fee/receipt.py
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Receipt(Base):
    __tablename__ = "receipt"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payment.id"), nullable=False)
    receipt_no = Column(String(64), nullable=False, unique=True, index=True)
    pdf_path = Column(String(1024), nullable=False)
    # allow nullable for migrations/tests where a created_by may not be supplied up-front
    created_by = Column(Integer, ForeignKey("user.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # NOTE: back_populates must match the attribute name on Payment (which is `receipts`)
    payment = relationship("Payment", back_populates="receipts")
