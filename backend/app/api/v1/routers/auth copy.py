# backend/app/api/v1/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserCreate, UserOut, Token
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from passlib.context import CryptContext
from app.core.config import settings
from datetime import datetime, timedelta
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # rudimentary; in prod add validations and email confirmation
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail={"code":"user_exists","message":"User exists"})
    hashed = get_password_hash(user_in.password)
    user = User(email=user_in.email, hashed_password=hashed, role=user_in.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code":"invalid_credentials","message":"Invalid email or password"})
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "expires_in": settings.access_token_expire_minutes * 60}
