# backend/app/schemas/auth_admin.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class AdminResetPassword(BaseModel):
    student_id: int = Field(..., gt=0)
    new_password: str = Field(..., min_length=8)
    email: Optional[EmailStr] = None
