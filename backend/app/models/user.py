# backend/app/models/user.py
"""
User model for authentication and RBAC.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Simple role string for now: admin, clerk, accountant, student, parent, etc.
    role = Column(String(50), nullable=False, default="accountant")

    is_active = Column(Boolean, default=True)

    # NEW: optional link to a Student record (for student/parent accounts)
    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=True,
        index=True,
    )

    # ORM relationship to Student; one user ↔ one student in this simple model
    student = relationship(
        "Student",
        back_populates="user",
        uselist=False,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
