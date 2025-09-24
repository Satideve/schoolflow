# backend/app/services/auth_service.py

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import oauth2_scheme, verify_access_token
from app.models.user import User

# Define the OAuth2 scheme (must match your token endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """
    Provide a SQLAlchemy session for auth dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate a bearer JWT, look up the user, and return it.
    Raises 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1) Verify & decode JWT
    try:
        payload = verify_access_token(token)
        user_id = int(payload.sub) if payload.sub is not None else None
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # 2) Fetch the user
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        raise credentials_exception

    return user
