# backend/app/schemas/student.py

from typing import Optional

from pydantic import BaseModel


class StudentCreate(BaseModel):
    name: str
    roll_number: str
    class_section_id: int


class StudentUpdate(BaseModel):
    """Fields allowed to be updated on a student."""
    name: Optional[str] = None
    roll_number: Optional[str] = None
    class_section_id: Optional[int] = None


class StudentOut(StudentCreate):
    id: int

    class Config:
        from_attributes = True
