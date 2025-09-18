# backend/app/api/v1/routers/pdf.py

from fastapi import APIRouter, Response
import pdfkit
from pathlib import Path

router = APIRouter()

@router.get("/pdf")
def generate_pdf():
    html = "<h1>Generated PDF</h1><p>Served via FastAPI.</p>"
    options = {
        "header-right": "Page [page] of [topage]",
        "encoding": "UTF-8"
    }

    # Correct path: backend/data/receipts
    output_dir = Path(__file__).resolve().parents[3] / "data" / "receipts"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "generated.pdf"
    pdfkit.from_string(html, str(output_path), options=options)

    return Response(content=output_path.read_bytes(), media_type="application/pdf")
