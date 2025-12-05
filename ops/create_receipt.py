# ops/create_receipt.py

"""
CLI/Webhook op to render a persisted receipt’s PDF.

Used by ReceiptService.create_receipt_and_render:
- Receipt row (with pdf_path) is created and flushed by the service.
- This script is then called with receipt_id to render the PDF at that path.
"""

from pathlib import Path
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.fee.receipt import Receipt
from app.services.pdf.context_loader import load_receipt_context
from app.services.pdf.renderer import render_receipt_pdf


def main(receipt_id: int) -> str:
    """
    Given an existing Receipt.id with a valid pdf_path,
    load its context, render the PDF, and return the path.
    """
    db: Session = SessionLocal()
    try:
        # 1) Fetch the receipt
        receipt = (
            db.query(Receipt)
            .filter(Receipt.id == receipt_id)
            .one()
        )

        pdf_path = receipt.pdf_path
        if not pdf_path:
            # Defensive fallback: should rarely happen because ReceiptService sets it.
            # Use a simple default in the receipts directory based on receipt_no.
            from app.core.config import settings

            base = Path(settings.receipts_path())
            base.mkdir(parents=True, exist_ok=True)
            filename = f"{receipt.receipt_no or 'REC-' + str(receipt.id)}.pdf"
            pdf_path = str(base / filename)
            receipt.pdf_path = pdf_path
            db.commit()
            db.refresh(receipt)

        # 2) Load context (cumulative totals via load_invoice_context) and render
        context = load_receipt_context(receipt_id, db)
        render_receipt_pdf(context, pdf_path)

        return pdf_path
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.ops.create_receipt <receipt_id>")
        sys.exit(1)

    rid = int(sys.argv[1])
    path = main(rid)
    print(f"✅ PDF regenerated at: {path}")
