# backend/app/schemas/auth.py

from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    sub: str | None = None
    role: str | None = None
