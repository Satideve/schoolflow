# backend/app/api/v1/dependencies.py

from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth_service import get_current_user


def get_db() -> Generator[Session, None, None]:
    """
    Provide a SQLAlchemy session to path operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require that the authenticated user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
