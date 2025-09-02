# backend/app/models/fee/payment.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base

class Payment(Base):
    __tablename__ = "payment"
    id = Column(Integer, primary_key=True, index=True)
    fee_invoice_id = Column(Integer, ForeignKey("fee_invoice.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    provider_txn_id = Column(String(255), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    status = Column(String(20), nullable=False)  # created, captured, failed
    idempotency_key = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("provider", "provider_txn_id", name="u_provider_txn"),)
