# backend/tests/api/test_invoice_download.py
import uuid
from decimal import Decimal
from httpx import Response


def _ensure_class_section(auth_client) -> int:
    """
    Ensure there is at least one class section available and return its id.
    Tries to create a lightweight test section if none exist.
    """
    # Try listing existing sections
    resp_list: Response = auth_client.get("/api/v1/class-sections/")
    if resp_list.status_code == 200:
        items = resp_list.json()
        if items:
            # Return first one's id
            return items[0].get("id") or items[0].get("pk")

    # Create a new section with all required fields (including academic_year)
    payload = {
        "name": f"TS-{uuid.uuid4().hex[:6]}",
        "grade": "Test",
        "academic_year": "2025-2026",
    }
    resp: Response = auth_client.post("/api/v1/class-sections/", json=payload)
    assert resp.status_code in (200, 201), f"Failed to create class section: {resp.status_code} {resp.text}"
    sec = resp.json()
    return sec.get("id") or sec.get("pk")


def test_create_and_download_invoice_pdf(auth_client):
    """
    End-to-end test:
    1. Ensure class_section exists (create one if missing)
    2. Create a student
    3. Create an invoice
    4. Download invoice PDF and validate response
    """
    # Ensure class section
    class_section_id = _ensure_class_section(auth_client)

    # Create a student
    student_payload = {
        "name": f"Test Student {uuid.uuid4().hex[:6]}",
        "roll_number": f"ROLL-{uuid.uuid4().hex[:6]}",
        "class_section_id": class_section_id,
    }
    sresp: Response = auth_client.post("/api/v1/students/", json=student_payload)
    assert sresp.status_code in (200, 201), f"student create failed: {sresp.status_code} {sresp.text}"
    student = sresp.json()
    student_id = student.get("id") or student.get("student_id") or student.get("pk")
    assert student_id is not None, "created student id missing"

    # Create an invoice for the student
    invoice_payload = {
        "student_id": student_id,
        "invoice_no": f"INV-DOWNLOAD-{uuid.uuid4().hex[:8].upper()}",
        "period": "2025-11",
        "amount_due": float(Decimal("1500.00")),
        "due_date": "2025-11-30",
    }
    resp: Response = auth_client.post("/api/v1/invoices/", json=invoice_payload)
    assert resp.status_code == 201, f"invoice create failed: {resp.status_code} {resp.text}"
    inv = resp.json()
    inv_id = inv["id"]

    # Download the invoice PDF
    dl = auth_client.get(f"/api/v1/invoices/{inv_id}/download")
    assert dl.status_code == 200, f"download failed: {dl.status_code} {dl.text}"

    # Ensure the response looks like a PDF
    content_type = dl.headers.get("content-type", "")
    assert "pdf" in content_type.lower() or dl.content[:4] == b"%PDF", "response not a PDF"
