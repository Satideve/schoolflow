# backend/app/schemas/class_section.py

from pydantic import BaseModel

class ClassSectionCreate(BaseModel):
    name: str
    academic_year: str

class ClassSectionOut(ClassSectionCreate):
    id: int

    class Config:
        from_attributes = True
