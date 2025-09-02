# backend/app/models/fee/fee_component.py
from sqlalchemy import Column, Integer, String
from app.db.base import Base

class FeeComponent(Base):
    __tablename__ = "fee_component"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(512), nullable=True)
