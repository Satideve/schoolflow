# backend/app/schemas/user.py
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "accountant"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    # NEW: optional student mapping
    student_id: Optional[int] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
