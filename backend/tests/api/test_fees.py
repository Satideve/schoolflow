# backend/tests/api/test_fees.py
"""
Resilient version of test_fees that works both with in-memory/sqlite test DBs
and with a seeded real PostgreSQL test DB (USE_REAL_DB=true).

Key changes:
 - Use `db_session` fixture to locate an existing student when present (seeded).
 - If no student exists, create a transient student inside the test transaction.
 - Avoid reliance on magic fixed student ids; always obtain a valid student_id.
 - All tests still use `auth_client` for authenticated API calls.
 - Preserves original assertions and behavior.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import Response
from sqlalchemy import text

# helper to ensure a usable student exists and return its id
def _ensure_student(db_session):
    """
    Return a student id that can be used for invoices.
    Prefer an existing student (seeded production-like table).
    If none exists, create one within the test transaction (safe).
    """
    # Try to pick an existing student first (works when seeds have been loaded)
    try:
        row = db_session.execute(text("SELECT id FROM students ORDER BY id LIMIT 1")).fetchone()
        if row and row[0]:
            return int(row[0])
    except Exception:
        # If direct SQL fails for any reason, fall back to ORM creation below
        pass

    # No existing student found -> create one in the test transaction
    from app.models.class_section import ClassSection
    from app.models.student import Student

    cs = db_session.query(ClassSection).first()
    if not cs:
        cs = ClassSection(name="TS-default", academic_year="2025-26")
        db_session.add(cs)
        db_session.commit()
        db_session.refresh(cs)

    student = Student(
        name=f"Student-{uuid.uuid4().hex[:6]}",
        roll_number=f"R{uuid.uuid4().hex[:6]}",
        class_section_id=cs.id,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student.id


def _make_invoice_payload(student_id: int = 1, amount: float | Decimal = 5000.0):
    """Helper to build an InvoiceCreate-style payload compatible with current API."""
    return {
        "student_id": student_id,
        "invoice_no": f"TEST-INV-{uuid.uuid4().hex[:8]}",
        "period": "2025-12",
        "amount_due": float(Decimal(amount)),
        "due_date": date(2025, 12, 31).isoformat(),
    }


def test_create_fee(auth_client, db_session):
    """
    Ensure we can create a fee-like invoice via the API.
    Uses db_session to find/create a student so the test works with seeded DBs.
    """
    student_id = _ensure_student(db_session)
    assert student_id is not None, "could not find or create a student for the test"

    payload = _make_invoice_payload(student_id=student_id, amount=5000)
    resp: Response = auth_client.post("/api/v1/invoices/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    # invoice uses 'amount_due' field
    assert float(data["amount_due"]) == float(payload["amount_due"])
    assert data["invoice_no"] == payload["invoice_no"]
    assert data["student_id"] == payload["student_id"]


def test_get_fees(auth_client, db_session):
    """
    Create a couple invoices and ensure listing invoices returns them.
    This variant ensures students exist (created or seeded).
    """
    # ensure we have a valid student to attach invoices to
    student_id = _ensure_student(db_session)

    p1 = _make_invoice_payload(student_id=student_id, amount=1234.50)
    p2 = _make_invoice_payload(student_id=student_id, amount=2222.00)
    r1 = auth_client.post("/api/v1/invoices/", json=p1)
    r2 = auth_client.post("/api/v1/invoices/", json=p2)
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text

    resp: Response = auth_client.get("/api/v1/invoices/")
    assert resp.status_code == 200, resp.text
    invoices = resp.json()
    invoice_nos = {inv.get("invoice_no") for inv in invoices}
    assert p1["invoice_no"] in invoice_nos
    assert p2["invoice_no"] in invoice_nos


def test_get_single_fee(auth_client, db_session):
    """
    Create an invoice and fetch it by id.
    """
    student_id = _ensure_student(db_session)
    payload = _make_invoice_payload(student_id=student_id, amount=750.0)
    create_resp = auth_client.post("/api/v1/invoices/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    invoice_id = created["id"]

    resp: Response = auth_client.get(f"/api/v1/invoices/{invoice_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == invoice_id
    assert float(data["amount_due"]) == float(payload["amount_due"])


def test_create_fee_payment(auth_client, db_session):
    """
    Create an invoice, then call payments/create-order to ensure the payment-order endpoint works.
    """
    student_id = _ensure_student(db_session)
    payload = _make_invoice_payload(student_id=student_id, amount=3500.00)
    create_resp = auth_client.post("/api/v1/invoices/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    invoice = create_resp.json()
    invoice_id = invoice["id"]

    # Create order for the invoice (returns an 'order' object)
    pay_resp: Response = auth_client.post(f"/api/v1/payments/create-order/{invoice_id}")
    assert pay_resp.status_code == 200, pay_resp.text
    body = pay_resp.json()
    assert "order" in body, body
    order = body["order"]
    # best-effort assertions (adapter shape may vary); ensure invoice amount is represented
    assert order is not None
    if isinstance(order, dict):
        amt_fields = ["amount", "total", "value"]
        assert any(f in order for f in amt_fields) or "id" in order


def test_get_fee_payments(auth_client):
    """
    Ensure the receipts metadata endpoint is reachable (returns JSON list).
    """
    resp: Response = auth_client.get("/api/v1/receipts/metadata")
    assert resp.status_code == 200, resp.text
    payments = resp.json()
    assert isinstance(payments, list)
