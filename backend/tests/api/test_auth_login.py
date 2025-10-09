# backend/tests/api/test_auth_login.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.schemas.user import UserCreate

# -------------------------------
# 1) In-memory DB setup (shared in-memory)
# -------------------------------
# Use StaticPool so the same in-memory DB is shared across connections/sessions.
ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)

# Create all tables once on the shared in-memory engine
Base.metadata.create_all(bind=ENGINE)

# -------------------------------
# 2) Override get_db dependency (as a fixture)
# -------------------------------
def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# We'll apply the override inside the client fixture so startup ordering is safe.
# (Avoid creating TestClient(app) at import-time; do it inside fixture.)

# -------------------------------
# 3) Test client fixture using overridden DB
# -------------------------------
@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    # cleanup override after test
    app.dependency_overrides.pop(get_db, None)

# -------------------------------
# 4) Fixtures
# -------------------------------
@pytest.fixture
def create_user(client):
    payload = UserCreate(email="u@test.com", password="pass1234", role="student")
    resp = client.post("/api/v1/auth/register", json=payload.dict())
    assert resp.status_code == 200
    return payload

# -------------------------------
# 5) Tests
# -------------------------------
def test_login_success(create_user, client):
    form = {"username": "u@test.com", "password": "pass1234"}
    resp = client.post("/api/v1/auth/login", data=form)
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and body["token_type"] == "bearer"

@pytest.mark.parametrize("form,code", [
    ({"username": "u@test.com","password":"wrong"}, 401),
    ({"username": "nobody@test.com","password":"pass1234"}, 401),
    ({"username": "u@test.com"}, 422),
])
def test_login_failures(form, code, client):
    resp = client.post("/api/v1/auth/login", data=form)
    assert resp.status_code == code
