# backend/scripts/debug_invoice_download.py
import requests, json

BASE = "http://localhost:8000"
INVOICE_ID = 19

s = requests.Session()
r = s.post(
    f"{BASE}/api/v1/auth/login",
    data={"username": "admin@example.com", "password": "ChangeMe123!"}
)
r.raise_for_status()

dl = s.get(f"{BASE}/api/v1/invoices/{INVOICE_ID}/download")
print("Download ->", dl.status_code, "bytes=", len(dl.content))
print("Content-Type:", dl.headers.get("content-type"))
