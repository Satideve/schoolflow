# backend/app/db/session.py

from .base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.core.config import settings
import os
import sys

# Determine DB URL from settings (settings.database_url should already be resolved from env)
database_url = getattr(settings, "database_url", None) or os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError("No database URL found in settings.database_url or DATABASE_URL env var")

# For SQLite we must pass check_same_thread=False when used across threads (fastapi/testclient)
connect_args = {}
if str(database_url).startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create engine with future flag
engine = create_engine(database_url, future=True, connect_args=connect_args)

# DEBUG: print engine/url and current ENV so we can trace import-time DB selection (keeps appearing in pytest logs)
print("=== IMPORT-TIME DB DEBUG ===", file=sys.stderr, flush=True)
print("ENV DATABASE_URL =", os.environ.get("DATABASE_URL"), file=sys.stderr, flush=True)
try:
    print("settings.database_url =", getattr(settings, "database_url", "<no attr>"), file=sys.stderr, flush=True)
    print("engine.url =", repr(getattr(engine, "url", "<no engine.url>")), file=sys.stderr, flush=True)
except Exception as _e:
    print("error while printing engine info:", _e, file=sys.stderr, flush=True)
print("=== END IMPORT-TIME DB DEBUG ===", file=sys.stderr, flush=True)

# Regular scoped session for application use (e.g. dependency get_db)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, future=True)
)

# Export a plain sessionmaker intended for tests (fixtures / TestClient to share)
# Tests often expect to import TestingSessionLocal to create transactions / sessions.
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

def get_db():
    """
    FastAPI dependency: yields a Session from the scoped SessionLocal.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
