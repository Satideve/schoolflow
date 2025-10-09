# backend/app/api/dependencies/auth.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.api.v1.routers.auth import get_current_user as _get_current_user

# Re-export get_current_user so existing imports keep working
get_current_user = _get_current_user

def require_roles(*roles: str):
    def role_checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        return user
    return role_checker
