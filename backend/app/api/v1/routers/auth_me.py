# C:\coding_projects\dev\schoolflow\backend\app\api\v1\routers\auth_me.py
from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserOut:
    """
    Return the authenticated user's profile.
    Uses UserOut schema and returns the ORM user instance directly.
    """
    return current_user
