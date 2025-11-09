# backend/tests/services/test_pdf_context_totals.py

import os
import math
import pytest
from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.pdf.context_loader import load_invoice_context, load_receipt_context

pytestmark = pytest.mark.skipif(
    os.getenv("USE_REAL_DB", "").lower() != "true",
    reason="Requires USE_REAL_DB=true against Postgres with seeded/E2E data",
)

TOL = 1e-6

def _approx_equal(a, b, tol=TOL):
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) <= tol and math.isfinite(float(a)) and math.isfinite(float(b))
    except Exception:
        return False

def test_invoice_context_totals_real_db():
    db = SessionLocal()
    try:
        inv_id = db.execute(text("SELECT id FROM fee_invoice ORDER BY id DESC LIMIT 1")).scalar_one()
        ctx = load_invoice_context(inv_id, db)

        # Ensure all keys exist
        assert {"items_total", "total_due", "paid_amount", "balance"} <= set(ctx.keys())

        # total_due should match invoice.amount_due when present
        inv_amt = db.execute(text("SELECT amount_due FROM fee_invoice WHERE id=:i"), {"i": inv_id}).scalar_one()
        if inv_amt is not None:
            assert _approx_equal(ctx["total_due"], inv_amt)

        # balance must be total_due - paid_amount
        if ctx["total_due"] is not None and ctx["paid_amount"] is not None:
            assert _approx_equal(
                ctx["balance"],
                float(ctx["total_due"]) - float(ctx["paid_amount"])
            )
    finally:
        db.close()

def test_receipt_context_totals_real_db():
    db = SessionLocal()
    try:
        rec_id = db.execute(text("SELECT id FROM receipt ORDER BY id DESC LIMIT 1")).scalar_one()
        ctx = load_receipt_context(rec_id, db)

        assert {"items_total", "total_due", "paid_amount", "balance"} <= set(ctx.keys())

        if ctx["total_due"] is not None and ctx["paid_amount"] is not None:
            assert _approx_equal(
                ctx["balance"],
                float(ctx["total_due"]) - float(ctx["paid_amount"])
            )
    finally:
        db.close()
