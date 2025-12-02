# backend/app/schemas/user.py
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """
    Payload for creating a new user via /auth/register or admin APIs.

    - email: login email
    - password: plain text password (will be hashed server-side)
    - role: defaults to "student" for safety; backend may override/validate.
    - student_id: optional link to an existing Student row
    """
    email: EmailStr
    password: str
    role: str = "student"
    student_id: Optional[int] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    # optional student mapping (used for student dashboards / “My invoices”)
    student_id: Optional[int] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
