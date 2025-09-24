# backend/app/services/pdf/renderer.py

"""
PDF renderer using pdfkit (wkhtmltopdf).
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

# Directory where Jinja2 will look for templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
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
            print(f"[DEBUG] wkhtmltopdf resolved to: {p_path}")
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

def render_receipt_pdf(context: Dict, output_path: str, options: Optional[Dict] = None) -> str:
    """
    Render receipt HTML from template and convert to PDF.
    Returns the path to the written PDF (string).

    This function:
      - Renders the Jinja2 template into HTML
      - Locates a wkhtmltopdf binary (honoring env var and settings)
      - Ensures output directory exists
      - Calls pdfkit to write the PDF
      - Raises informative errors on failure
    """
    # 1) Render HTML via Jinja2
    tpl = env.get_template("receipts/receipt.html")
    html = tpl.render(**context)

    # 2) Determine wkhtmltopdf binary path
    try:
        wkhtml_path = _find_wkhtmltopdf(settings.wkhtmltopdf_cmd)
    except FileNotFoundError as e:
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

    # 5) Ensure output directory exists
    out_path = Path(output_path) if output_path else Path("/tmp/receipts/unknown.pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 6) Generate the PDF
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

