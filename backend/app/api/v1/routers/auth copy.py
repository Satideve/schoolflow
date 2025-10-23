# backend/app/api/v1/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import logging

# from app.schemas.user import UserCreate, UserOut, Token
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Custom BearerAuth to align OpenAPI spec with Swagger UI ---
from fastapi.security import HTTPBearer


class BearerAuth(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    def openapi_scheme(self):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }


# Use this for all protected endpoints
bearer_scheme = BearerAuth(auto_error=True)


# bcrypt has a hard limit of 72 bytes for the password input.
# We apply a deterministic, reversible-by-truncation policy:
#   - encode to UTF-8, truncate to 72 bytes, decode ignoring truncated trailing bytes
# Doing the same at hash-and-verify avoids nondeterministic failures during
# passlib/backend detection or hashing.
_BCRYPT_MAX_BYTES = 72


def _truncate_password_to_bcrypt_limit(plain: str) -> str:
    """
    Ensure we never pass >72 bytes to bcrypt (UTF-8 byte length).
    If truncation is needed, log a debug message and return truncated string.
    """
    if plain is None:
        return plain
    try:
        b = plain.encode("utf-8")
    except Exception:
        # Fallback: coerce to str then to bytes
        b = str(plain).encode("utf-8", errors="ignore")
    if len(b) <= _BCRYPT_MAX_BYTES:
        return plain
    # truncate bytes then decode ignoring incomplete utf-8 tail
    truncated = b[:_BCRYPT_MAX_BYTES].decode("utf-8", errors="ignore")
    logger.debug(
        "Truncating password for bcrypt: original_bytes=%d truncated_bytes=%d",
        len(b),
        len(truncated.encode("utf-8")),
    )
    return truncated


def get_password_hash(password: str) -> str:
    """
    Hash a password for storage. Truncate deterministically to bcrypt limit
    to avoid runtime errors from underlying bcrypt backend.
    """
    if password is None:
        raise ValueError("password must be provided")
    safe_pw = _truncate_password_to_bcrypt_limit(password)
    try:
        return pwd_context.hash(safe_pw)
    except ValueError as ve:
        # Defensive: wrap passlib/bcrypt ValueError into a clearer HTTP-friendly exception
        logger.exception("bcrypt ValueError while hashing password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_password", "message": str(ve)},
        )


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.
    We apply the same truncation to the plain input so verify is consistent
    with the hash created at registration time.
    """
    if plain is None:
        return False
    safe_plain = _truncate_password_to_bcrypt_limit(plain)
    try:
        return pwd_context.verify(safe_plain, hashed)
    except ValueError:
        # Rare: if bcrypt backend raises due to unexpected input, treat as mismatch
        logger.exception("bcrypt ValueError while verifying password")
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate JWT from Authorization: Bearer <token>.
    Using Security(...) ensures BearerAuth is declared in OpenAPI,
    so Swagger UI attaches the Authorization header automatically.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Missing or invalid auth scheme"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_token", "message": "Token missing subject"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Could not validate credentials"},
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "User not found"},
        )
    return user


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # rudimentary; in prod add validations and email confirmation
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=400, detail={"code": "user_exists", "message": "User exists"}
        )
    # hash password (truncation applied inside helper)
    hashed = get_password_hash(user_in.password)
    user = User(email=user_in.email, hashed_password=hashed, role=user_in.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# @router.post("/login", response_model=Token)
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     # OAuth2PasswordRequestForm provides form_data.username and form_data.password (form-encoded)
#     user = db.query(User).filter(User.email == form_data.username).first()
#     if not user or not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail={"code": "invalid_credentials", "message": "Invalid email or password"},
#         )
#     token = create_access_token({"sub": str(user.id), "role": user.role})
#     return {
#         "access_token": token,
#         "token_type": "bearer",
#         "expires_in": settings.access_token_expire_minutes * 60,
#     }
# backend/app/api/v1/routers/auth.py


logger = logging.getLogger("app.auth")

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm provides form_data.username and form_data.password (form-encoded)
    # Add debug logging so tests can show why login succeeds/fails.
    username = getattr(form_data, "username", None)
    pw = getattr(form_data, "password", None)
    logger.debug("login: received username=%r password_len=%s", username, len(pw or ""))

    user = db.query(User).filter(User.email == username).first()
    if user:
        logger.debug("login: found user id=%s email=%s hash_len=%d is_active=%s",
                     user.id, user.email, len(user.hashed_password or ""), user.is_active)
    else:
        logger.debug("login: user not found for username=%r", username)

    # Wrap verify_password to surface exceptions (bcrypt/passlib can raise on some backends)
    try:
        password_ok = bool(user) and verify_password(pw, user.hashed_password)
    except Exception as exc:
        logger.exception("login: exception when verifying password for username=%r: %s", username, exc)
        password_ok = False

    logger.debug("login: password_ok=%s", password_ok)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Invalid email or password"},
        )
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


