# backend/app/services/pdf/context_loader.py

from sqlalchemy.orm import Session
from app.models.fee.receipt import Receipt
from app.models.fee.payment import Payment
from app.models.fee.fee_invoice import FeeInvoice
from app.models.student import Student

def load_receipt_context(receipt_id: int, db: Session) -> dict:
    receipt = db.query(Receipt).filter_by(id=receipt_id).first()
    if not receipt:
        raise ValueError(f"Receipt {receipt_id} not found")

    if not receipt.pdf_path:
        receipt.pdf_path = f"app/data/receipts/RCT-{receipt.id:04d}.pdf"
        db.commit()  # Persist the synthesized path

    payment = db.query(Payment).filter_by(id=receipt.payment_id).first()
    invoice = db.query(FeeInvoice).filter_by(id=payment.fee_invoice_id).first()
    student = db.query(Student).filter_by(id=invoice.student_id).first()

    return {
        "receipt": {
            "receipt_no": receipt.receipt_no,
            "pdf_path": receipt.pdf_path,
        },
        "payment": {
            "amount": float(payment.amount),
            "provider": payment.provider,
            "provider_txn_id": payment.provider_txn_id,
            "status": payment.status,
        },
        "invoice": {
            "period": invoice.period,
            "amount_due": float(invoice.amount_due),
            "due_date": invoice.due_date.strftime("%d-%b-%Y"),
        },
        "student": {
            "name": student.name,
            "id": student.id,
        },
    }

# Reuse receipt context loader for invoices to keep behavior unchanged
load_invoice_context = load_receipt_context
