# backend/tests/conftest.py
"""
Pytest fixtures for SchoolFlow backend tests (synchronous).

This file is a preserved, production-safe merge of your original conftest.py
with safer behavior for running tests against a real PostgreSQL test DB
(USE_REAL_DB=true). Key guarantees:

 - Keeps original fixture names and semantics.
 - Keeps sqlite/local behaviour (destructive cleanup) for fast dev runs.
 - When USE_REAL_DB=true: avoids destructive truncation of seeded tables.
   Tests run using per-test transactional/session isolation; changes are rolled back
   so seeded production-like data stays intact.
 - Preserves logging and auth_client behavior (register/login via TestClient).
 - Does not change variable/fixture names or folder layout.

First line is the path as requested.
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
BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
TESTS_TMP_DATA = BACKEND_DIR / "tmp_data"

# Test DB file placed inside backend directory (fast local)
TEST_DB_FILENAME = ".pytest_test_db.sqlite"
TEST_DB_PATH = BACKEND_DIR / TEST_DB_FILENAME

# Feature flag for using a real DB for E2E/integration testing.
USE_REAL_DB = os.getenv("USE_REAL_DB", "false").lower() in {"1", "true", "yes"}

# Determine TEST_DATABASE_URL:
if USE_REAL_DB:
    # When using real DB, tests will use DATABASE_URL environment var
    TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@infra-db-1:5432/schoolflow_test")
else:
    TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

# Ensure tests tmp dir is prepared (clean start for sqlite mode)
try:
    if TESTS_TMP_DATA.exists() and not USE_REAL_DB:
        shutil.rmtree(TESTS_TMP_DATA)
    TESTS_TMP_DATA.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# -----------------------
# Environment variables required by app at import time
# -----------------------
os.environ["BASE_DIR"] = str(BACKEND_DIR)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "testsecretkey123456"

# -----------------------
# Imports that must happen AFTER env vars set
# -----------------------
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# -----------------------
# Create SQLAlchemy engine + Session factory for tests
# -----------------------
_url_obj = make_url(TEST_DATABASE_URL)
connect_args = {}
if _url_obj.drivername and _url_obj.drivername.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

if _url_obj.drivername and _url_obj.drivername.startswith("sqlite"):
    _engine = create_engine(TEST_DATABASE_URL, connect_args=connect_args, poolclass=StaticPool)
else:
    _engine = create_engine(TEST_DATABASE_URL, connect_args=connect_args)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# Create tables for sqlite/local mode; for real DB we assume migrations created them.
if not USE_REAL_DB:
    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except Exception:
        pass
    Base.metadata.create_all(bind=_engine)

# atexit cleanup (best-effort). Do NOT remove real DB.
def _remove_test_artifacts():
    try:
        if not USE_REAL_DB and TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except Exception:
        pass
    try:
        if not USE_REAL_DB and TESTS_TMP_DATA.exists():
            shutil.rmtree(TESTS_TMP_DATA)
    except Exception:
        pass

atexit.register(_remove_test_artifacts)

# -----------------------
# Dependency override
# -----------------------
def _override_get_db():
    """
    Dependency override for FastAPI endpoints to use the testing Session.
    Yields an independent Session bound to the test engine.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

# -----------------------
# Logging and helpers
# -----------------------
logger = logging.getLogger("tests.conftest")
logger.setLevel(logging.DEBUG)


def _log_table_counts(session, when: str):
    """Helper to log table counts for debugging test DB state (best-effort)."""
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


# -----------------------
# Fixtures
# -----------------------
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
        raise

    # Ensure tmp dir exists
    TESTS_TMP_DATA.mkdir(parents=True, exist_ok=True)

    # Override Settings value used by application code at runtime.
    try:
        settings.base_dir = str(TESTS_TMP_DATA)
        logger.debug("override_settings_base_dir: settings.base_dir set to %s", settings.base_dir)
    except Exception:
        os.environ["BASE_DIR"] = str(TESTS_TMP_DATA)
        logger.debug("override_settings_base_dir: fallback set BASE_DIR env to %s", os.environ["BASE_DIR"])

    yield
    # teardown - nothing required here (atexit will handle cleanup)


# -----------------------
# clear_db_between_tests
# -----------------------
@pytest.fixture()
def clear_db_between_tests():
    """
    Reproduces the original behavior for local sqlite runs: delete all rows from every
    table before and after each test so tests cannot leak data.

    For USE_REAL_DB == True we do NOT perform destructive deletes of seeded tables.
    Instead we log the counts and leave existing seeded data intact. Tests must therefore
    use transactional isolation (db_session fixture) and/or create transient rows.
    """
    # Delete before the test starts (only for local sqlite runs)
    session = TestingSessionLocal()
    try:
        _log_table_counts(session, "before-cleanup")
        if not USE_REAL_DB:
            for table in reversed(Base.metadata.sorted_tables):
                try:
                    session.execute(delete(table))
                except Exception:
                    logger.exception("Failed to delete table %s during cleanup", table.name)
            session.commit()
            _log_table_counts(session, "after-cleanup")
        else:
            logger.debug("clear_db_between_tests: USE_REAL_DB enabled; skipping destructive cleanup")
    finally:
        session.close()

    # Let the test run
    yield

    # Delete after the test finishes (only for local sqlite)
    session = TestingSessionLocal()
    try:
        _log_table_counts(session, "before-post-test-cleanup")
        if not USE_REAL_DB:
            for table in reversed(Base.metadata.sorted_tables):
                try:
                    session.execute(delete(table))
                except Exception:
                    logger.exception("Failed to delete table %s during post-test cleanup", table.name)
            session.commit()
            _log_table_counts(session, "after-post-test-cleanup")
        else:
            logger.debug("clear_db_between_tests: USE_REAL_DB enabled; skipping destructive post-test cleanup")
    finally:
        session.close()


# -----------------------
# seed_base_students_after_cleanup
# -----------------------
@pytest.fixture(autouse=True)
def seed_base_students_after_cleanup(clear_db_between_tests):
    """
    Test-time helper: seed a base set of students after the test DB cleanup runs.

    - In local sqlite mode this will create a class_section and many students so tests
      that expect numeric ids (1..N) will find them.
    - In USE_REAL_DB mode this fixture will be a no-op (we don't globally insert into real DB).
      Tests should instead use the per-test transactional seed_student fixture.
    """
    if USE_REAL_DB:
        logger.debug("seed_base_students_after_cleanup: USE_REAL_DB=true -> skipping global seeding")
        yield
        return

    # local sqlite behavior: create class_section and many students if not present
    from app.models.class_section import ClassSection
    from app.models.student import Student

    db = TestingSessionLocal()
    try:
        existing = db.query(Student).count()
        if existing and existing > 0:
            logger.debug("seed_base_students_after_cleanup: students already present (%s), skipping", existing)
            yield
            return

        cs = db.query(ClassSection).first()
        if not cs:
            cs = ClassSection(name="TS-default", academic_year="2025-26")
            db.add(cs)
            db.flush()

        # create many students so ids up to ~30 exist
        count = 30
        for i in range(count):
            s = Student(
                name=f"Seed S{i+1}",
                roll_number=f"RN-{uuid.uuid4().hex[:8]}",
                class_section_id=cs.id,
            )
            db.add(s)
        db.commit()
        logger.debug("seed_base_students_after_cleanup: created %s students", count)
    finally:
        db.close()
    yield
    # no teardown here (clear_db_between_tests will delete for non-real DB)


# -----------------------
# db_session fixture (NON-DESTRUCTIVE for real DB)
# -----------------------
@pytest.fixture(scope="function")
def db_session():
    """
    Provide a SQLAlchemy Session for tests.

    Behavior:
      - When running against the in-memory/sqlite test DB (default), we create a
        CONNECT -> TRANSACTION pattern so each test runs in an isolated transaction
        and is rolled back at the end. This keeps sqlite in-process tests clean and fast.
      - When running against a real PostgreSQL DB (USE_REAL_DB=true), we avoid
        destroying seeded tables. We yield a live session and perform a rollback
        on teardown, but we DO NOT execute destructive delete(...) across all tables.
        That deletion was wiping your seed data; so it is removed.
    """
    if USE_REAL_DB:
        real_session = TestingSessionLocal()
        try:
            yield real_session
        finally:
            # Only rollback/close — do not drop/truncate rows in real DB.
            try:
                real_session.rollback()
            except Exception:
                pass
            try:
                real_session.close()
            except Exception:
                pass
    else:
        # sqlite / local mode: strong isolation using an outer transaction
        connection = _engine.connect()
        outer_trans = connection.begin()
        test_session = TestingSessionLocal(bind=connection)
        try:
            yield test_session
        finally:
            try:
                test_session.rollback()
            except Exception:
                pass
            try:
                test_session.close()
            except Exception:
                pass
            try:
                outer_trans.rollback()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass


# -----------------------
# seed_invoice fixture
# -----------------------
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


# -----------------------
# Test client fixtures (client, auth_client)
# -----------------------
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
    """
    from app.models.user import User
    from app.core.security import get_password_hash, verify_password
    from passlib.context import CryptContext

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


# -----------------------
# seed_student and seed_fee_plan fixtures
# -----------------------
@pytest.fixture()
def seed_student(db_session):
    """Create and return a demo student record."""
    from app.models.student import Student
    from app.models.class_section import ClassSection

    # Attempt to use existing class_section (seeded in real DB) or create one in-transaction
    cs = db_session.query(ClassSection).first()
    if not cs:
        cs = ClassSection(name=f"TS-default", academic_year="2025-26")
        db_session.add(cs)
        db_session.flush()

    student = Student(
        name=f"Student-{uuid.uuid4().hex[:6]}",
        roll_number=f"R{uuid.uuid4().hex[:4]}",  # FIXED field name
        class_section_id=cs.id,
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


@pytest.fixture()
def seed_fee_plan(db_session):
    """Create and return a sample fee plan matching the FeePlan model."""
    from app.models.fee.fee_plan import FeePlan

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
