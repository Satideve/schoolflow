# backend/app/ops/full_inspect.py
"""
Standalone DB + filesystem inspection tool for invoices/payments/receipts.

Run inside the backend container:
  docker-compose exec backend sh -c "python /app/backend/ops/full_inspect.py"

This script uses SessionLocal (standalone DB session) so it won't be affected by
FastAPI dependency overrides used in tests.
"""
from pathlib import Path
from pprint import pprint
from app.db.session import SessionLocal
from app.models.fee.receipt import Receipt
from app.models.fee.payment import Payment
from app.models.fee.fee_invoice import FeeInvoice
import os
import fnmatch

# Candidate directories to search for generated PDFs
CANDIDATES = [
    Path("/app/backend/app/data/receipts"),
    Path("/app/backend/app/data/invoices"),
    Path("/app/backend/data/receipts"),
    Path("/app/backend/data/invoices"),
    Path("/app/backend/tmp_data/app/data/receipts"),
    Path("/app/backend/tmp_data/app/data/invoices"),
    Path("/app/backend/tmp_data/receipts"),
    Path("/app/backend/tmp_data/invoices"),
    Path("/app/backend"),
]

def fs_search(patterns, base_dirs=CANDIDATES, max_results=200):
    results = []
    for base in base_dirs:
        try:
            if not base.exists():
                continue
            # Walk and match patterns
            for root, dirs, files in os.walk(base):
                for p in patterns:
                    for name in fnmatch.filter(files, p):
                        full = Path(root) / name
                        results.append((p, str(full), full.stat().st_size))
                        if len(results) >= max_results:
                            return results
        except Exception as e:
            results.append(("error", f"{base}: {e}", 0))
    return results

def fmt(obj):
    return {k: getattr(obj, k) if hasattr(obj, k) else None for k in ["id", "receipt_no", "payment_id", "pdf_path", "created_by", "created_at"]}

def main():
    print("=== Running full_inspect.py ===")
    print(f"PWD: {Path.cwd()}")
    print(f"BASE_DIR env? {os.getenv('BASE_DIR')}")
    print()

    db = SessionLocal()
    try:
        # Receipts
        receipts = db.query(Receipt).order_by(Receipt.id.desc()).limit(50).all()
        print(f"\n--- Receipts (last {len(receipts)}) ---")
        if receipts:
            for r in receipts:
                print(f"Receipt id={r.id} receipt_no={getattr(r,'receipt_no',None)} payment_id={getattr(r,'payment_id',None)} pdf_path={getattr(r,'pdf_path',None)} created_by={getattr(r,'created_by',None)} created_at={getattr(r,'created_at',None)}")
        else:
            print("No receipts found")

        # Payments
        payments = db.query(Payment).order_by(Payment.id.desc()).limit(50).all()
        print(f"\n--- Payments (last {len(payments)}) ---")
        if payments:
            for p in payments:
                print(f"Payment id={p.id} fee_invoice_id={getattr(p,'fee_invoice_id',None)} provider={getattr(p,'provider',None)} provider_txn_id={getattr(p,'provider_txn_id',None)} amount={getattr(p,'amount',None)} status={getattr(p,'status',None)} created_at={getattr(p,'created_at',None)}")
        else:
            print("No payments found")

        # Invoices
        invoices = db.query(FeeInvoice).order_by(FeeInvoice.id.desc()).limit(100).all()
        print(f"\n--- Invoices (last {len(invoices)}) ---")
        if invoices:
            for i in invoices:
                print(f"Invoice id={i.id} invoice_no={getattr(i,'invoice_no',None)} student_id={getattr(i,'student_id',None)} amount_due={getattr(i,'amount_due',None)} status={getattr(i,'status',None)} created_at={getattr(i,'created_at',None)}")
        else:
            print("No invoices found")

        # Filesystem scan for receipts/invoices
        print("\n--- Filesystem scan: REC-*.pdf and INV-*.pdf ---")
        fs_results = fs_search(["REC-*.pdf", "INV-*.pdf", "INV-INV-*.pdf"], max_results=500)
        if fs_results:
            for pat, path, size in fs_results:
                print(f"{pat:12} {size:8d}  {path}")
        else:
            print("No matching PDF files found in candidate directories.")

        # Cross-check DB pdf_path fields against FS existence
        print("\n--- Cross-check receipt.pdf_path existence ---")
        for r in receipts:
            p = getattr(r, "pdf_path", None)
            if not p:
                print(f"Receipt id={r.id} has empty pdf_path")
                continue
            resolved = Path(p)
            # If relative path, resolve against common base dirs for convenience
            exists = resolved.exists()
            if not exists and not resolved.is_absolute():
                # try common bases
                alt_exists = False
                for base in CANDIDATES:
                    cand = base / p
                    if cand.exists():
                        alt_exists = True
                        resolved = cand
                        break
                exists = alt_exists
            print(f"Receipt id={r.id} pdf_path='{p}' -> exists={exists} resolved='{resolved}'")
    finally:
        db.close()
    print("\n=== Done ===")

if __name__ == "__main__":
    main()
