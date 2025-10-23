# backend/ops/cleanup_fees.py
"""
Cleanup receipts, payments, and invoices for a fresh start.
WARNING: This deletes data irreversibly. Use only in dev/test.
"""

from app.db.session import get_db
from app.repositories.fee_repo import list_receipts, list_payments
from app.repositories.invoice_repo import list_invoices

db = next(get_db())

# --- Delete Receipts ---
receipts = list_receipts(db)
for r in receipts:
    print(f"Deleting Receipt id={r.id} receipt_no={r.receipt_no}")
    db.delete(r)
db.commit()

# --- Delete Payments ---
payments = list_payments(db)
for p in payments:
    print(f"Deleting Payment id={p.id} provider_txn_id={getattr(p,'provider_txn_id',None)}")
    db.delete(p)
db.commit()

# --- Delete Invoices ---
invoices = list_invoices(db)
for i in invoices:
    print(f"Deleting Invoice id={i.id} invoice_no={getattr(i,'invoice_no',None)}")
    db.delete(i)
db.commit()

print("DB cleanup done.")
