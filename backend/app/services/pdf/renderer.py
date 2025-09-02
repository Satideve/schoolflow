# backend/app/services/pdf/renderer.py
"""
PDF renderer using pdfkit (wkhtmltopdf).
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape
import pdfkit
from app.core.config import settings
from pathlib import Path
from typing import Dict

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

def render_receipt_pdf(context: Dict, output_path: str) -> str:
    """
    Render receipt HTML from template and convert to PDF.
    Returns the path to written PDF.
    """
    tpl = env.get_template("receipts/receipt.html")
    html = tpl.render(**context)
    wkhtml_path = settings.wkhtmltopdf_cmd or None
    config = pdfkit.configuration(wkhtmltopdf=wkhtml_path) if wkhtml_path else None
    options = {"enable-local-file-access": None}
    pdfkit.from_string(html, output_path, configuration=config, options=options)
    return output_path
