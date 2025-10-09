# backend/tests/api/test_invoice_download.py
import os
import shutil
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

def test_create_and_download_invoice_pdf(auth_client):
    """
    End-to-end (sync) test:
      1. Create a new invoice via API (authenticated)
      2. Download its PDF via API
    """
    client = auth_client  # pre-authenticated TestClient from conftest

    payload = {
        "student_id": 101,
        "invoice_no": "INV-DOWNLOAD-001",
        "period": "2025-12",
        "amount_due": float(Decimal("3500.00")),
        "due_date": datetime(2025, 12, 31, 0, 0).isoformat(),  # use datetime
        "payment": {  # added optional payment
            "provider": "manual",
            "amount": float(Decimal("3500.00")),
            "status": "captured",
        }
    }

    # Ensure invoices directory exists and is clean (matches conftest/tmp_data)
    tmp_data = Path(__file__).parent / "tmp_data"
    invoices_dir = tmp_data / "invoices"
    if invoices_dir.exists():
        shutil.rmtree(invoices_dir)
    invoices_dir.mkdir(parents=True, exist_ok=True)

    # Create invoice
    resp = client.post("/api/v1/invoices/", json=payload)
    assert resp.status_code == 201, f"invoice create failed: {resp.status_code} {resp.text}"
    data = resp.json()
    invoice_id = data["id"]

    # Download invoice PDF
    download_resp = client.get(f"/api/v1/invoices/{invoice_id}/download")
    assert download_resp.status_code == 200, f"download failed: {download_resp.status_code} {download_resp.text}"
    assert download_resp.headers.get("content-type") == "application/pdf"
    assert download_resp.content and len(download_resp.content) > 0


def test_download_invoice_pdf_not_found(auth_client):
    """
    Downloading a non-existent invoice should return 404.
    """
    client = auth_client

    # Ensure invoices directory is empty
    tmp_data = Path(__file__).parent / "tmp_data"
    invoices_dir = tmp_data / "invoices"
    if invoices_dir.exists():
        shutil.rmtree(invoices_dir)
    invoices_dir.mkdir(parents=True, exist_ok=True)

    resp = client.get("/api/v1/invoices/999999/download")
    assert resp.status_code == 404
    # Exact text without trailing period, matching router
    assert resp.json()["detail"] == "Invoice not found"
