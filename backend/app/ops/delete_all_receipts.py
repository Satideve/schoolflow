# backend/app/ops/delete_all_receipts.py

from app.db.session import SessionLocal
from app.models.fee.receipt import Receipt

def main():
    db = SessionLocal()
    deleted = db.query(Receipt).delete()
    db.commit()
    print(f"🧹 Deleted {deleted} receipt(s) from the database")

if __name__ == "__main__":
    main()
