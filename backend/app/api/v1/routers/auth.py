# backend/app/api/v1/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, Security, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import logging
from typing import List, Optional

# from app.schemas.user import UserCreate, UserOut, Token
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from app.models.student import Student


logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Custom BearerAuth to align OpenAPI spec with Swagger UI ---
from fastapi.security import HTTPBearer


class BearerAuth(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        # allow callers to decide whether absence of header should auto-error
        super().__init__(auto_error=auto_error)

    def openapi_scheme(self):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }


# Use this for all protected endpoints.
# Set auto_error=False so we can gracefully fallback to cookie-based tokens
# (useful for Swagger UI and browser clients that store token in a cookie).
bearer_scheme = BearerAuth(auto_error=False)


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
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    request: Request = None,
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate JWT from either:
      - Authorization: Bearer <token> header (preferred), OR
      - access_token cookie (convenience for browser/Swagger UI).

    Note: bearer_scheme is configured with auto_error=False so that this function
    can examine cookies as a fallback rather than having the Security layer raise
    immediately. Tests that supply Authorization header continue to work unchanged.
    """
    token = None

    # 1) Header (preferred)
    if credentials and getattr(credentials, "scheme", "").lower() == "bearer":
        token = credentials.credentials

    # 2) Cookie fallback (useful for browser-based clients / Swagger UI convenience)
    if not token and request is not None:
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            # Cookie may contain "Bearer <token>" or just "<token>"
            if cookie_token.lower().startswith("bearer "):
                token = cookie_token.split(" ", 1)[1].strip()
            else:
                token = cookie_token.strip()

    # 3) No token -> unauthorized
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Missing or invalid auth credentials"},
        )

    # 4) Validate token payload
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

    # 5) Fetch user
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "User not found"},
        )
    return user


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """
    Public registration endpoint.

    Rules:
    - Always creates a 'student' user (ignores incoming role to avoid elevation).
    - If student_id is provided:
        * Student must exist.
        * No other user may already be linked to this student_id.
    """

    # 1) Ensure email is unique
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # 2) Validate student_id linkage if provided
    student_id: Optional[int] = payload.student_id

    if student_id is not None:
        # Check that the student exists
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student with id {student_id} does not exist",
            )

        # Ensure no other user is already linked to this student
        existing_link = (
            db.query(User)
            .filter(User.student_id == student_id)
            .first()
        )
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This student already has a linked user account",
            )

    # 3) Hash password and force safe role
    hashed = get_password_hash(payload.password)

    user = User(
        email=payload.email,
        hashed_password=hashed,
        role="student",        # force student for public registration
        is_active=True,
        student_id=student_id, # may be None
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


logger = logging.getLogger("app.auth")


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm provides form_data.username and form_data.password (form-encoded)
    # Add debug logging so tests can show why login succeeds/fails.
    username = getattr(form_data, "username", None)
    pw = getattr(form_data, "password", None)
    logger.debug("login: received username=%r password_len=%s", username, len(pw or ""))

    user = db.query(User).filter(User.email == username).first()
    if user:
        logger.debug(
            "login: found user id=%s email=%s hash_len=%d is_active=%s",
            user.id,
            user.email,
            len(user.hashed_password or ""),
            user.is_active,
        )
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

    # Also set cookie-friendly value in response so browser/Swagger UI will send it automatically.
    # Note: for local dev and Swagger we keep httponly=False; in production consider httponly=True and secure=True.
    if response is not None:
        max_age = settings.access_token_expire_minutes * 60
        # store the raw token (get_current_user accepts either "Bearer <token>" or raw token)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=False,
            secure=False,
            samesite="lax",
            max_age=max_age,
        )

    response_payload = {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }

    return response_payload
