# # backend/app/ops/create_receipt.py

# from sqlalchemy.orm import Session
# from app.db.session import SessionLocal
# from app.services.fee.receipt_service import create_receipt_and_render

# def main(payment_id: int, receipt_no: str | None = None):
#     db: Session = SessionLocal()
#     try:
#         receipt = create_receipt_and_render(db, payment_id=payment_id, receipt_no=receipt_no)
#         print(f"✅ Receipt created: {receipt.receipt_no}")
#         print(f"📄 PDF path: {receipt.pdf_path}")
#     finally:
#         db.close()

# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         print("Usage: python create_receipt.py <payment_id> [receipt_no]")
#         sys.exit(1)

#     pid = int(sys.argv[1])
#     rno = sys.argv[2] if len(sys.argv) > 2 else None
#     main(pid, rno)

# backend/app/ops/create_receipt.py

"""
CLI/Webhook op to render a persisted receipt’s PDF.
This standalone script uses only the DB session, repository, and PDF layers,
so it won’t import back into the service and cause a circular import.
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
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).one()
        pdf_path = receipt.pdf_path

        # 2) Load context and render
        context = load_receipt_context(receipt_id, db)
        render_receipt_pdf(context, pdf_path)

        return pdf_path
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python create_receipt.py <receipt_id>")
        sys.exit(1)

    rid = int(sys.argv[1])
    path = main(rid)
    print(f"✅ PDF regenerated at: {path}")
