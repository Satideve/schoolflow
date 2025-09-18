# backend/app/models/class_section.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class ClassSection(Base):
    __tablename__ = "class_sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    academic_year = Column(String, index=True, nullable=False)

    students = relationship(
        "Student",
        back_populates="class_section",
        cascade="all, delete-orphan"
    )
