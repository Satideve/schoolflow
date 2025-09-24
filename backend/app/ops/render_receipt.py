# backend/app/ops/render_receipt.py

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.pdf.context_loader import load_receipt_context
from app.services.pdf.renderer import render_receipt_pdf

def main(receipt_id: int):
    db: Session = SessionLocal()
    try:
        context = load_receipt_context(receipt_id, db)
        output_path = render_receipt_pdf(context, output_path=context["receipt"]["pdf_path"])
        print(f"✅ Receipt PDF generated at: {output_path}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    rid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    main(rid)
