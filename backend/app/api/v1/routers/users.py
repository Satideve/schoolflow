# C:\coding_projects\dev\schoolflow\backend\app\api\v1\routers\users.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut
from app.api.dependencies.auth import get_current_user, require_roles

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)


@router.get(
    "/",
    response_model=List[UserOut],
    dependencies=[Depends(require_roles("admin"))],
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all users in the system.

    - Admin-only (enforced by require_roles("admin")).
    """
    return db.query(User).all()


@router.get(
    "/{user_id}",
    response_model=UserOut,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single user by ID.

    - Admin can see any user.
    - Non-admin can only see themselves (their own id).
    """
    # Self or admin check
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
