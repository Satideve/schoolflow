# backend/app/services/pdf/renderer.py

"""
PDF renderer using pdfkit (wkhtmltopdf).

This module provides two explicit functions:
 - render_receipt_pdf(context, output_path, options=None)
 - render_invoice_pdf(context, output_path, options=None)

They share the same wkhtmltopdf discovery and pdfkit configuration,
but explicitly load different Jinja templates so invoice vs receipt
templates receive the correct context and won't raise undefined errors.

Also fixes template search path resolution so Jinja loads templates
from app/templates (project root) irrespective of the current working dir.
"""
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Optional

import pdfkit
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

# Templates dir: go up from this file to the project root and use 'app/templates'
# renderer.py lives at app/services/pdf/renderer.py -> parents[2] => project root /app
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

# Expose a few safe builtins to templates so template authors can use them
# without having to modify templates or rely on implicit environment globals.
env.globals.update(
    {
        "getattr": getattr,
        "len": len,
        "str": str,
    }
)


def _find_wkhtmltopdf(preferred: Optional[str] = None) -> str:
    """
    Locate a usable wkhtmltopdf binary.

    Order of checks:
      1. WKHTMLTOPDF_CMD environment variable
      2. explicit `preferred` value (usually settings.wkhtmltopdf_cmd)
      3. system PATH via shutil.which('wkhtmltopdf')
      4. known common install locations for wkhtmltopdf

    Raises FileNotFoundError with a helpful message when not found.
    """
    candidates = []

    # 1. Env var (highest priority)
    env_val = os.environ.get("WKHTMLTOPDF_CMD")
    if env_val:
        candidates.append(env_val)

    # 2. Preferred from settings
    if preferred:
        candidates.append(preferred)

    # 3. PATH
    which_path = shutil.which("wkhtmltopdf")
    if which_path:
        candidates.append(which_path)

    # 4. Common locations (Linux containers / common packages)
    common_paths = [
        "/usr/local/bin/wkhtmltopdf",
        "/usr/bin/wkhtmltopdf",
        "/opt/wkhtmltox/bin/wkhtmltopdf",
        "/usr/local/sbin/wkhtmltopdf",
        "/bin/wkhtmltopdf",
    ]
    candidates.extend(common_paths)

    tried = []
    for p in candidates:
        if not p:
            continue
        tried.append(p)
        try:
            p_path = Path(p)
        except Exception:
            continue
        if p_path.is_file() and os.access(str(p_path), os.X_OK):
            logger.debug("Using wkhtmltopdf binary at: %s", str(p_path))
            return str(p_path)

    # Nothing found
    msg = (
        "No wkhtmltopdf executable found. Tried paths: "
        + ", ".join(tried)
        + ".\n"
        "Please install wkhtmltopdf (the patched Qt build) and/or set the "
        "WKHTMLTOPDF_CMD environment variable or `settings.wkhtmltopdf_cmd` to "
        "the binary path. See: https://github.com/JazzCore/python-pdfkit/wiki/Installing-wkhtmltopdf"
    )
    logger.error(msg)
    raise FileNotFoundError(msg)


def _guess_output_path_for_template(template_path: str, context: Dict) -> str:
    """
    If the caller didn't supply an explicit output_path, guess a sensible
    server-side path based on the template type and context.

    - Invoices -> backend/app/data/invoices/<invoice_no or invoice_id>.pdf
    - Receipts  -> backend/app/data/receipts/<receipt_no or receipt_id>.pdf
    """
    template_path = (template_path or "").lstrip("/")

    if template_path.startswith("invoices/"):
        invoices_dir = settings.invoices_path()
        # prefer invoice_no in context, else fall back to invoice object id
        invoice_no = context.get("invoice_no")
        if not invoice_no:
            inv = context.get("invoice")
            try:
                invoice_no = getattr(inv, "invoice_no", None)
            except Exception:
                invoice_no = None
        filename = f"{invoice_no}.pdf" if invoice_no else f"invoice-{context.get('invoice_id', 'unknown')}.pdf"
        return str((invoices_dir / filename).resolve())

    if template_path.startswith("receipts/"):
        receipts_dir = settings.receipts_path()
        receipt_no = context.get("receipt_no")
        if not receipt_no:
            # sometimes context may carry a 'receipt' object
            r = context.get("receipt")
            try:
                receipt_no = getattr(r, "receipt_no", None)
            except Exception:
                receipt_no = None
        filename = f"{receipt_no}.pdf" if receipt_no else f"receipt-{context.get('receipt_id', 'unknown')}.pdf"
        return str((receipts_dir / filename).resolve())

    # Fallback - put into /tmp
    return str(Path("/tmp") / f"{(context.get('invoice_no') or context.get('receipt_no') or 'doc')}.pdf")


def _render_template_to_pdf(template_path: str, context: Dict, output_path: Optional[str], options: Optional[Dict] = None) -> str:
    """
    Internal helper: render a Jinja template to HTML, then to PDF using pdfkit.
    `template_path` is relative to templates dir, e.g. "receipts/receipt.html".

    If `output_path` is falsy, we auto-choose a server-side path under the
    configured invoices/receipts directories so generated PDFs are persisted
    in the repo's data volume.
    """
    # 1) Render HTML via Jinja2
    tpl = env.get_template(template_path)
    html = tpl.render(**context)

    # 2) Determine wkhtmltopdf binary path
    try:
        wkhtml_path = _find_wkhtmltopdf(settings.wkhtmltopdf_cmd)
    except FileNotFoundError:
        raise

    # 3) Create pdfkit configuration
    config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)

    # 4) Merge default options
    default_options = {
        "enable-local-file-access": None,
        "print-media-type": None,
    }
    merged_options = default_options.copy()
    if options:
        merged_options.update(options)

    # 5) If no explicit output_path provided, pick the correct server-side folder
    if not output_path:
        output_path = _guess_output_path_for_template(template_path, context)

    out_path = Path(output_path)
    # 6) Ensure output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 7) Generate the PDF
    try:
        pdfkit.from_string(html, str(out_path), configuration=config, options=merged_options)
    except OSError as exc:
        logger.exception("OS error when calling wkhtmltopdf: %s", exc)
        raise RuntimeError(f"Failed generating PDF due to OS error: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error while generating PDF: %s", exc)
        raise RuntimeError(f"Failed generating PDF: {exc}") from exc

    logger.debug("PDF written to %s using wkhtmltopdf=%s", out_path, wkhtml_path)
    return str(out_path)


def render_receipt_pdf(context: Dict, output_path: Optional[str], options: Optional[Dict] = None) -> str:
    """
    Render receipt HTML from 'receipts/receipt.html' template and convert to PDF.
    Returns the path to the written PDF (string).
    """
    return _render_template_to_pdf("receipts/receipt.html", context, output_path, options)


def render_invoice_pdf(context: Dict, output_path: Optional[str], options: Optional[Dict] = None) -> str:
    """
    Render invoice HTML from 'invoices/invoice.html' template and convert to PDF.
    Returns the path to the written PDF (string).

    We keep this separate to ensure the invoice template receives invoice-specific
    context variables and won't get the wrong template (receipt) by accident.
    """
    return _render_template_to_pdf("invoices/invoice.html", context, output_path, options)
