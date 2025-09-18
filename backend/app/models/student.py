# backend/app/models/student.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    roll_number = Column(String, unique=True, index=True, nullable=False)
    class_section_id = Column(Integer, ForeignKey("class_sections.id"), nullable=False)

    class_section = relationship(
        "ClassSection",
        back_populates="students"
    )
