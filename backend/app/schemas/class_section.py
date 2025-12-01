# backend/app/schemas/class_section.py

from typing import Optional

from pydantic import BaseModel


class ClassSectionCreate(BaseModel):
    name: str
    academic_year: str


class ClassSectionUpdate(BaseModel):
    """Fields allowed to be updated on a class section."""
    name: Optional[str] = None
    academic_year: Optional[str] = None


class ClassSectionOut(ClassSectionCreate):
    id: int

    class Config:
        from_attributes = True
