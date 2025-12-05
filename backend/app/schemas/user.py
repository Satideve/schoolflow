# backend/app/schemas/user.py
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    # Optional role from caller.
    # - For student-linked users, we will force "student"
    #   regardless of what is passed.
    # - For admin/clerk, we will respect what is passed (if valid).
    role: Optional[str] = None

    # Optional mapping to a student
    student_id: Optional[int] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    # optional student mapping
    student_id: Optional[int] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
