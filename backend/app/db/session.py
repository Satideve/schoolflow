# backend/app/db/session.py

# from .base import Base
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, scoped_session
# from app.core.config import settings

# engine = create_engine(settings.database_url, future=True)
# SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# backend/app/db/session.py

from .base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.core.config import settings
import os
import sys

# Create engine from settings
engine = create_engine(settings.database_url, future=True)

# TEMP DEBUG: print engine/url and current ENV so we can trace import-time DB selection
# These prints are intentionally simple and flushed immediately so they appear in pytest logs.
print("=== IMPORT-TIME DB DEBUG ===", file=sys.stderr, flush=True)
print("ENV DATABASE_URL =", os.environ.get("DATABASE_URL"), file=sys.stderr, flush=True)
try:
    print("settings.database_url =", getattr(settings, "database_url", "<no attr>"), file=sys.stderr, flush=True)
    # engine.url may not be string-y identical across dialect/URL objects, but repr helps
    print("engine.url =", repr(getattr(engine, "url", "<no engine.url>")), file=sys.stderr, flush=True)
except Exception as _e:
    print("error while printing engine info:", _e, file=sys.stderr, flush=True)
print("=== END IMPORT-TIME DB DEBUG ===", file=sys.stderr, flush=True)

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
