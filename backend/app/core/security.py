# app/core/security.py

from passlib.context import CryptContext

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
