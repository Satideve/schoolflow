# backend/app/models/fee/fee_invoice_item.py

from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class FeeInvoiceItem(Base):
    __tablename__ = "fee_invoice_item"

    id = Column(Integer, primary_key=True, index=True)

    # Link to parent invoice
    fee_invoice_id = Column(
        Integer,
        ForeignKey("fee_invoice.id"),
        nullable=False,
        index=True,
    )

    # Human-friendly description of the line item
    description = Column(String(255), nullable=False)

    # Amount for this line item
    amount = Column(Numeric(10, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ORM relationship back to FeeInvoice (we will add FeeInvoice.items later)
    invoice = relationship("FeeInvoice", back_populates="items")
