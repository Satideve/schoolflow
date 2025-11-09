# backend/tests/api/test_invoice_totals_parity.py
"""
Verifies that when amount_due is 0/None, the service auto-fills it from
the summed fee plan components (items_total), and the API response fields
(`items_total`, `total_due`, `paid_amount`, `balance`, `items`) are consistent.
"""

import uuid
from decimal import Decimal
from httpx import Response


def test_invoice_amount_autofill_matches_items_total(auth_client, seed_student, seed_fee_plan):
    """
    1) Create an invoice with amount_due = 0 (placeholder).
    2) Expect API to return items (from plan components), items_total,
       and amount_due == items_total, total_due == items_total, paid_amount is None/0,
       and balance is None/0 (no payments yet).
    3) Download the invoice PDF and ensure it's available.
    """
    invoice_no = f"INV-AUTOFILL-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "student_id": seed_student.get("id") or seed_student.get("student_id") or seed_student.get("pk"),
        "plan_id": seed_fee_plan.get("id"),  # harmless extra field if your schema ignores it
        "invoice_no": invoice_no,
        "period": "2025-11",
        "amount_due": float(Decimal("0.00")),  # trigger auto-fill from items_total
        "due_date": "2025-11-30T00:00:00Z",
    }

    # Create invoice
    resp: Response = auth_client.post("/api/v1/invoices/", json=payload)
    assert resp.status_code == 201, resp.text
    inv = resp.json()
    inv_id = inv["id"]

    # Must have line items (from plan components)
    assert inv.get("items"), f"Expected items from fee plan components for invoice {inv_id}"
    items_total = inv.get("items_total")
    assert items_total is not None, "items_total should be computed"
    assert float(inv["amount_due"]) == float(items_total), "amount_due should auto-fill to items_total"
    assert float(inv["total_due"]) == float(items_total), "total_due should match items_total"
    # no payments yet
    assert inv.get("paid_amount") in (None, 0.0)
    assert inv.get("balance") in (None, 0.0)

    # Download PDF (should exist after creation/render)
    dl = auth_client.get(f"/api/v1/invoices/{inv_id}/download")
    assert dl.status_code == 200, dl.text
    ctype = dl.headers.get("content-type", "").lower()
    assert "pdf" in ctype
    assert len(dl.content) > 1000  # basic sanity check
