# backend/tests/api/test_invoices.py
import tempfile
import os
import shutil
from pathlib import Path
from types import SimpleNamespace
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.core.config import settings

# --- Use a temporary file-backed SQLite DB (avoids sqlite in-memory connection scoping issues) ---
_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_tmp_db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


# Override get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Prepare dummy users
admin_user = SimpleNamespace(id=1, role="admin")
student_user = SimpleNamespace(id=2, role="student")

# Default override: admin
def override_current_user_admin():
    return admin_user


app.dependency_overrides[get_current_user] = override_current_user_admin

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_database_and_storage():
    """
    Session-scoped fixture to create DB tables and a temporary invoices storage
    directory. Cleans up DB file and tmp data on teardown.
    """
    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Redirect file storage to a temp dir inside the tests tree
    tmp_data = Path(__file__).parent / "tmp_data"
    invoices_dir = tmp_data / "invoices"
    if tmp_data.exists():
        shutil.rmtree(tmp_data)
    invoices_dir.mkdir(parents=True, exist_ok=True)

    # Monkey-patch base_dir for config so services use the test tmp_data path
    settings.base_dir = str(tmp_data)

    yield

    # Teardown: drop tables and remove temp files
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass
    if tmp_data.exists():
        shutil.rmtree(tmp_data)

    # Close and remove the temp sqlite file
    try:
        os.close(_tmp_db_fd)
    except Exception:
        pass
    try:
        os.unlink(_tmp_db_path)
    except Exception:
        pass


@pytest.fixture(scope="function", autouse=True)
def session_scope():
    """
    Ensure each test uses a fresh transactional scope. Commits after the test's
    successful execution to make objects visible to other parts of the test
    harness if needed.
    """
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()


def test_create_invoice():
    payload = {
        "student_id": 1,
        "invoice_no": "INV-TEST-001",
        "period": "2025-11",
        "amount_due": 1500.50,
        "due_date": date(2025, 11, 30).isoformat(),
    }
    resp = client.post("/api/v1/invoices/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["invoice_no"] == payload["invoice_no"]
    assert data["student_id"] == payload["student_id"]
    assert "id" in data
