# backend/app/ops/update_receipt_path.py

from app.db.session import SessionLocal
from app.models.fee.receipt import Receipt

def main():
    db = SessionLocal()
    receipt = db.query(Receipt).filter_by(id=1).first()
    if receipt:
        receipt.pdf_path = "app/data/receipts/RCT-2025-0001.pdf"
        db.commit()
        print("✅ DB updated with new PDF path")
    else:
        print("❌ Receipt with ID 1 not found")

if __name__ == "__main__":
    main()
