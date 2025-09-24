# app/core/security.py

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

# Defines the OAuth2 bearer scheme for all token‐protected endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Configure PassLib to use bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a plaintext password against the stored bcrypt hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


class TokenPayload(BaseModel):
    """
    JWT payload model.
    Use standard 'sub' (subject) for user identifier to align with issuer.
    """
    sub: str
    role: str | None = None


def verify_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT access token, returning its payload as a TokenPayload.
    Raises JWTError if invalid.
    """
    try:
        data: dict[str, Any] = jwt.decode(
            token,
            settings.secret_key,       # align with config Settings field name
            algorithms=["HS256"],      # issuer uses HS256
        )
        # print("[verify_access_token] decoded keys:", list(data.keys()))  # DEBUG
        return TokenPayload(**data)
    except JWTError as err:
        # Bubble up JWT errors for caller to handle uniformly
        raise err
