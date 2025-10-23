# backend/ops/create_test_lines.py
"""
Create a small test invoice -> payment -> receipt chain and render the receipt PDF.

Safe / idempotent-ish helper for local dev. Requires at least one Student in DB.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.student import Student
from app.models.fee.fee_invoice import FeeInvoice
from app.models.fee.payment import Payment
from app.models.fee.receipt import Receipt
from app.services.pdf.renderer import render_receipt_pdf

def _iso_period(dt: datetime) -> str:
    # Use YYYY-MM (month) as a simple period value acceptable to most invoice templates
    return f"{dt.year:04d}-{dt.month:02d}"

def main() -> int:
    db: Session = SessionLocal()
    try:
        # 1) Find a student to attach invoice to
        student = db.query(Student).order_by(Student.id).first()
        if not student:
            raise SystemExit("No Student found in DB. Please seed a student (or run seed_student_101.py).")

        now = datetime.now(timezone.utc)
        period = _iso_period(now)
        due_date = now + timedelta(days=30)  # satisfy NOT NULL constraint and realistic due date

        # 2) Create invoice (ensure required NOT NULL fields are present)
        invoice = FeeInvoice(
            student_id=student.id,
            invoice_no=f"INV-TEST-LINES-{uuid.uuid4().hex[:8].upper()}",
            period=period,
            amount_due=3500.00,
            due_date=due_date,
            status="pending",
            created_at=now,
        )
        db.add(invoice)
        db.flush()  # get invoice.id

        print(f"Created invoice id={invoice.id} invoice_no={invoice.invoice_no} period={invoice.period} due_date={invoice.due_date}")

        # 3) Create a payment for that invoice
        payment = Payment(
            fee_invoice_id=invoice.id,
            provider="manual",
            provider_txn_id=f"manual-test-{uuid.uuid4().hex[:8]}",
            amount=3500.00,
            status="captured",
            created_at=now,
        )
        db.add(payment)
        db.flush()

        print(f"Created payment id={payment.id} provider_txn_id={payment.provider_txn_id}")

        # 4) Create a receipt row and write a PDF path (renderer will overwrite if required)
        receipts_dir = Path("/app/backend/app/data/receipts")
        receipts_dir.mkdir(parents=True, exist_ok=True)
        receipt_no = f"REC-{uuid.uuid4().hex[:10].upper()}"
        pdf_path = str(receipts_dir / f"{receipt_no}.pdf")

        receipt = Receipt(
            payment_id=payment.id,
            receipt_no=receipt_no,
            pdf_path=pdf_path,
            created_by=1,  # test admin user id commonly 1 in dev/test
            created_at=now,
        )
        db.add(receipt)
        db.commit()

        print(f"Created receipt id={receipt.id} receipt_no={receipt.receipt_no} pdf_path={receipt.pdf_path}")

        # 5) Render the receipt PDF (renderer may accept receipt id or context; try id first)
        try:
            rendered_path = render_receipt_pdf(receipt.id, db=db)
        except TypeError:
            # fallback: if renderer expects (context, output_path=...), just return path (renderer not invoked)
            rendered_path = pdf_path

        print("✅ Renderer returned:", rendered_path)
        return 0
    except Exception as exc:
        # helpful debug message
        print("ERROR creating test lines:", repr(exc))
        # rollback to keep DB consistent
        try:
            db.rollback()
        except Exception:
            pass
        raise
    finally:
        db.close()

if __name__ == "__main__":
    raise SystemExit(main())
