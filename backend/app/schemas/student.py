# backend/app/schemas/student.py

from pydantic import BaseModel

class StudentCreate(BaseModel):
    name: str
    roll_number: str
    class_section_id: int

class StudentOut(StudentCreate):
    id: int

    class Config:
        from_attributes = True
