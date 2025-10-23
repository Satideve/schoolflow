# C:\coding_projects\dev\schoolflow\backend\tests\conftest.py

"""
Pytest fixtures for SchoolFlow backend tests (synchronous).

This file sets up a SQLite file-backed database (so threads can safely access it),
creates tables, overrides the FastAPI `get_db` dependency so API endpoints
use the test DB, and provides sync TestClient fixtures used by integration tests.

IMPORTANT FIX: Some Settings validation expects BASE_DIR to point to a directory
that contains the `app` package. To satisfy that validation at import time we
set the BASE_DIR env var to the backend project directory (which contains `app`)
before importing the FastAPI app. Later, inside a session-scoped fixture, we
override `settings.base_dir` to point at the tests tmp_data directory used for
receipts/invoices. This preserves Settings validation while routing file writes
to an isolated test folder.
"""
import logging
import os
import pathlib
import atexit
import shutil
import uuid
import pytest

# -----------------------
# Paths & test directories
# -----------------------
# backend directory (parent of tests/)
BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
# tests tmp_data (where receipts/invoices will be written during tests)
TESTS_TMP_DATA = BACKEND_DIR / "tmp_data"

# Test DB file placed inside backend directory
TEST_DB_FILENAME = ".pytest_test_db.sqlite"
TEST_DB_PATH = BACKEND_DIR / TEST_DB_FILENAME
# TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

USE_REAL_DB = os.getenv("USE_REAL_DB", "false").lower() in {"1", "true", "yes"}

if USE_REAL_DB:
    TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@infra-db-1:5432/schoolflow")
else:
    TEST_DATABASE_URL = "sqlite:///./.pytest_test_db.sqlite"


# Ensure tests tmp dir is prepared (clean start)
try:
    if TESTS_TMP_DATA.exists():
        shutil.rmtree(TESTS_TMP_DATA)
    TESTS_TMP_DATA.mkdir(parents=True, exist_ok=True)
except Exception:
    # best-effort; if this fails tests will show errors later
    pass

# -----------------------
# Environment variables required by app at import time
# -----------------------
# Ensure BASE_DIR points to a directory that contains `app` so Settings validation passes.
# BACKEND_DIR contains the `app` package (e.g. /app/backend in container).
os.environ["BASE_DIR"] = str(BACKEND_DIR)
# Database and secret used for tests
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "testsecretkey123456"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

# Import the application AFTER env vars are set so pydantic Settings validate correctly.
from app.main import app
from app.db.base import Base
from app.db.session import get_db

# -----------------------
# Database engine + session factory for tests
# -----------------------
# Ensure prior DB file is removed (clean start)
try:
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
except Exception:
    pass

# _engine = create_engine(
#     TEST_DATABASE_URL,
#     connect_args={"check_same_thread": False},
#     poolclass=StaticPool,
# )

# detect DB type & set sqlite-only connect args only when appropriate
from sqlalchemy.engine.url import make_url

_db_url = TEST_DATABASE_URL  # existing var in your conftest
_url_obj = make_url(_db_url)
connect_args = {}
if _url_obj.drivername and _url_obj.drivername.startswith("sqlite"):
    # sqlite in-process requires this; postgres doesn't accept it
    connect_args = {"check_same_thread": False}

_engine = create_engine(_db_url, connect_args=connect_args)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_engine,
)

# Create tables once for the test session
Base.metadata.create_all(bind=_engine)

# Register atexit cleanup - best-effort removal of test DB file and tmp_data
def _remove_test_artifacts():
    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except Exception:
        pass
    try:
        if TESTS_TMP_DATA.exists():
            shutil.rmtree(TESTS_TMP_DATA)
    except Exception:
        pass

atexit.register(_remove_test_artifacts)

# -----------------------
# Override dependency
# -----------------------
def _override_get_db():
    """
    Dependency override for FastAPI endpoints to use the testing Session.
    Each call yields an independent Session bound to the file-backed DB.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _override_get_db

# -----------------------
# Fixtures
# -----------------------
logger = logging.getLogger("tests.conftest")
logger.setLevel(logging.DEBUG)


@pytest.fixture(scope="session", autouse=True)
def override_settings_base_dir():
    """
    Session-scoped autouse fixture that overrides settings.base_dir to point to
    the isolated tests tmp_data directory. We do this after importing the app so
    pydantic Settings validation (which runs at import) is satisfied.
    """
    try:
        from app.core.config import settings
    except Exception:
        # If import fails, allow test run to proceed and surface the error later
        raise

    # Ensure tmp dir exists
    TESTS_TMP_DATA.mkdir(parents=True, exist_ok=True)

    # Override Settings value used by application code at runtime.
    # Many modules read settings dynamically, so this will route file writes to tmp_data.
    try:
        settings.base_dir = str(TESTS_TMP_DATA)
        logger.debug("override_settings_base_dir: settings.base_dir set to %s", settings.base_dir)
    except Exception:
        # If Settings is frozen or doesn't allow assignment, set environment var fallback
        os.environ["BASE_DIR"] = str(TESTS_TMP_DATA)
        logger.debug("override_settings_base_dir: fallback set BASE_DIR env to %s", os.environ["BASE_DIR"])

    yield

    # teardown - nothing required here (atexit handles cleanup)


# @pytest.fixture(autouse=True)
@pytest.fixture()
def clear_db_between_tests():
    """
    Autouse fixture: run before every test to remove all rows from every table
    so tests cannot leak data to each other. Uses the same TestingSessionLocal
    as the app so deletions are visible to the TestClient.
    Also performs a cleanup pass after the test to be extra-safe.
    Logs table counts before/after cleanup to help debugging.
    """
    from sqlalchemy import delete, text

    def _log_table_counts(session, when: str):
        try:
            tbls = Base.metadata.sorted_tables
            logger.debug("%s: Base.metadata.sorted_tables: %s", when, [t.name for t in tbls])
            for t in tbls:
                try:
                    r = session.execute(text(f"SELECT COUNT(*) as c FROM \"{t.name}\"")).scalar_one()
                except Exception:
                    r = "<err>"
                logger.debug("%s: table=%s count=%s", when, t.name, r)
        except Exception:
            logger.exception("Failed to log table counts for %s", when)

    # Delete before the test starts
    session = TestingSessionLocal()
    try:
        _log_table_counts(session, "before-cleanup")
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(delete(table))
        session.commit()
        _log_table_counts(session, "after-cleanup")
    finally:
        session.close()

    # Let the test run
    yield

    # Delete after the test finishes (best-effort cleanup)
    session = TestingSessionLocal()
    try:
        _log_table_counts(session, "before-post-test-cleanup")
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(delete(table))
        session.commit()
        _log_table_counts(session, "after-post-test-cleanup")
    finally:
        session.close()

# proceed — add this fixture to backend/tests/conftest.py (place after clear_db_between_tests)

@pytest.fixture(autouse=True)
def seed_base_students_after_cleanup(clear_db_between_tests):
    """
    Test-time helper: seed a base set of students after the test DB cleanup runs.

    - This fixture depends on `clear_db_between_tests`, so it executes after
      the cleanup and will therefore survive into each test.
    - It creates a single ClassSection (if none exists) and then creates
      `count` students (unique roll_numbers) so tests that expect students
      with ids like 1,5,10,11,20 work reliably.
    - We keep this lightweight and idempotent (it will only insert when the
      students table is empty).
    """
    from app.models.class_section import ClassSection
    from app.models.student import Student
    from app.db.session import TestingSessionLocal
    import uuid

    db = TestingSessionLocal()
    try:
        # If students already exist for this test (some tests create their own),
        # don't reseed here.
        existing = db.query(Student).count()
        if existing and existing > 0:
            return

        # Ensure a ClassSection exists
        cs = db.query(ClassSection).first()
        if not cs:
            cs = ClassSection(name="TS-default", academic_year="2025-26")
            db.add(cs)
            db.flush()  # get cs.id

        # Create enough students so IDs up to `count` will exist
        # Tests reference ids up to ~20; create 30 to be safe.
        count = 30
        students = []
        for i in range(count):
            s = Student(
                name=f"Seed S{i+1}",
                roll_number=f"RN-{uuid.uuid4().hex[:8]}",
                class_section_id=cs.id,
            )
            students.append(s)
            db.add(s)
        db.commit()
        # No need to return anything; tests use their own fixtures as needed.
    finally:
        db.close()



@pytest.fixture(scope="function")
def db_session():
    """
    Provide a SQLAlchemy Session for tests.

    Ensures the DB is cleaned (all rows deleted) after each test so tests
    using fixed test data (invoice numbers, etc.) won't conflict.
    """
    from sqlalchemy import delete

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        try:
            db.rollback()
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(delete(table))
            db.commit()
        finally:
            db.close()


# --- New fixture: seed_invoice ---
@pytest.fixture(scope="function")
def seed_invoice(db_session, seed_student, seed_fee_plan):
    """
    Create and return a FeeInvoice linked to existing seed_student and seed_fee_plan.

    Returns a dict with keys expected by tests (id, invoice_no, amount_due, student_id, status).
    This fixture handles both cases where seed_student/seed_fee_plan are ORM objects or dicts.
    """
    from datetime import datetime
    from decimal import Decimal
    from app.models.fee.fee_assignment import FeeAssignment
    from app.models.fee.fee_invoice import FeeInvoice

    def _extract_id(obj):
        if obj is None:
            return None
        # dict-like
        if isinstance(obj, dict):
            return obj.get("id") or obj.get("student_id") or obj.get("pk")
        # ORM-like
        return getattr(obj, "id", getattr(obj, "student_id", None))

    student_id = _extract_id(seed_student)
    plan_id = _extract_id(seed_fee_plan)

    # Create a FeeAssignment linking student and plan (some services/readers expect this)
    assignment = FeeAssignment(
        student_id=student_id,
        fee_plan_id=plan_id,
        concession=Decimal("0.00"),
        note="test fixture assignment",
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    # Create a FeeInvoice
    invoice = FeeInvoice(
        student_id=student_id,
        invoice_no=f"INV-SEED-{uuid.uuid4().hex[:8].upper()}",
        period="2025-10",
        amount_due=Decimal("1500.00"),
        due_date=datetime(2025, 10, 31),
        status="pending",
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)

    return {
        "id": invoice.id,
        "invoice_no": invoice.invoice_no,
        "amount_due": float(invoice.amount_due),
        "student_id": invoice.student_id,
        "status": invoice.status,
    }
# --- End seed_invoice fixture ---


@pytest.fixture(scope="function")
def client():
    """
    Synchronous TestClient (useful for sync-style tests).
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def auth_client(db_session):
    """
    Synchronous TestClient pre-authenticated as an 'admin' user.

    - Ensures an admin user exists in the test DB (commits so the app session can see it).
    - Performs a real login via the /api/v1/auth/login endpoint to obtain a JWT.
    - Attaches Authorization header to the TestClient and yields it.

    IMPORTANT: we create the user via the API register endpoint (idempotent)
    so the user is visible to the same DB/session context the application uses.
    """
    # create or ensure user in test DB
    from app.models.user import User
    # Use the canonical security helper (not a router-level helper)
    from app.core.security import get_password_hash, verify_password

    email = "testadmin@example.com"
    password = "ChangeMe123!"
    role = "admin"

    # Quick local sanity checks and debug
    logger.debug(
        "TEST DEBUG: SECRET_KEY present? %s (len=%s)",
        bool(os.getenv("SECRET_KEY")),
        len(os.getenv("SECRET_KEY") or ""),
    )
    try:
        local_hashed = get_password_hash(password)
        from passlib.context import CryptContext

        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        ok = ctx.verify(password, local_hashed)
        logger.debug("TEST DEBUG: passlib hash/verify OK (hash_len=%s)", len(local_hashed))
    except Exception:
        logger.exception("TEST DEBUG: passlib bcrypt sanity check failed")

    # Use the TestClient to create the user via /register to ensure same DB visibility
    with TestClient(app) as test_client:
        register_payload = {"email": email, "password": password, "role": role}
        resp = test_client.post("/api/v1/auth/register", json=register_payload)
        if resp.status_code in (200, 201):
            logger.debug("auth_client: registered user via API: %s", email)
        elif resp.status_code == 400:
            logger.debug(
                "auth_client: register returned 400 (user exists), will ensure hash updated in DB session"
            )
            user = db_session.query(User).filter(User.email == email).first()
            if user:
                hashed = get_password_hash(password)
                if not verify_password(password, user.hashed_password):
                    logger.debug("auth_client: updating existing user's password hash")
                    user.hashed_password = hashed
                    user.is_active = True
                    db_session.add(user)
                    db_session.commit()
                    db_session.refresh(user)
            else:
                hashed = get_password_hash(password)
                user = User(email=email, hashed_password=hashed, role=role, is_active=True)
                db_session.add(user)
                db_session.commit()
                db_session.refresh(user)
        else:
            logger.debug("auth_client: register returned status %s: %s", resp.status_code, resp.text)
            user = db_session.query(User).filter(User.email == email).first()
            if not user:
                hashed = get_password_hash(password)
                user = User(email=email, hashed_password=hashed, role=role, is_active=True)
                db_session.add(user)
                db_session.commit()
                db_session.refresh(user)

        login_resp = test_client.post("/api/v1/auth/login", data={"username": email, "password": password})
        if login_resp.status_code != 200:
            user_row = db_session.query(User).filter(User.email == email).first()
            if user_row:
                logger.debug(
                    "auth_client: user in DB -> id=%s email=%s hash_len=%s",
                    user_row.id,
                    user_row.email,
                    len(user_row.hashed_password or ""),
                )
                try:
                    logger.debug(
                        "auth_client: local verify_password(password, stored_hash) -> %s",
                        verify_password(password, user_row.hashed_password),
                    )
                except Exception as e:
                    logger.exception("auth_client: local verify_password raised: %s", e)
            logger.debug("auth_client: login attempt returned status=%s text=%s", login_resp.status_code, login_resp.text)

        assert login_resp.status_code == 200, f"login failed in fixture: {login_resp.status_code} {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "auth_client fixture couldn't obtain access_token"

        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client

import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from app.models.student import Student
from app.models.fee.fee_plan import FeePlan

@pytest.fixture()
def seed_student(db_session):
    """Create and return a demo student record."""
    student = Student(
        name=f"Student-{uuid.uuid4().hex[:6]}",
        roll_number=f"R{uuid.uuid4().hex[:4]}",  # FIXED field name
        class_section_id=1,  # assuming a default class_section exists or add one if needed
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return {
        "id": student.id,
        "student_id": student.id,
        "name": student.name,
        "roll_number": student.roll_number,
    }


import uuid
from decimal import Decimal
import pytest
from app.models.fee.fee_plan import FeePlan

@pytest.fixture()
def seed_fee_plan(db_session):
    """Create and return a sample fee plan matching the FeePlan model."""
    plan = FeePlan(
        name=f"Plan-{uuid.uuid4().hex[:6]}",
        academic_year="2025-2026",
        frequency="annual",
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return {
        "id": plan.id,
        "name": plan.name,
        "academic_year": plan.academic_year,
        "frequency": plan.frequency,
    }

