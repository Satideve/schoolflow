import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.repositories import fee_repo
from app.models.fee.fee_plan import FeePlan
from app.models.fee.fee_component import FeeComponent
from app.models.fee.fee_plan_component import FeePlanComponent
from app.models.fee.fee_invoice import FeeInvoice
from app.models.fee.payment import Payment
from app.models.fee.receipt import Receipt

@pytest.mark.usefixtures("db_session")
class TestFeeRepo:

    def test_create_and_get_fee_plan(self, db_session):
        plan = fee_repo.create_fee_plan(db_session, "Plan A", "2025-26", "monthly")
        assert isinstance(plan, FeePlan)
        fetched = fee_repo.get_fee_plan(db_session, plan.id)
        assert fetched.id == plan.id
        assert fee_repo.get_fee_plan(db_session, 9999) is None

    def test_create_fee_component_and_add_to_plan(self, db_session):
        plan = fee_repo.create_fee_plan(db_session, "Plan B", "2025-26", "yearly")
        comp = fee_repo.create_fee_component(db_session, "Tuition", "Tuition fees")
        mapping = fee_repo.add_component_to_plan(db_session, plan.id, comp.id, Decimal("5000.00"))
        assert isinstance(mapping, FeePlanComponent)
        assert mapping.amount == Decimal("5000.00")

    def test_create_invoice_and_payment_and_receipt(self, db_session):
        inv = fee_repo.create_invoice(
            db_session,
            student_id=1,
            period="Apr-2025",
            amount_due=Decimal("7500.00"),
            due_date=datetime.utcnow() + timedelta(days=30),
        )
        assert isinstance(inv, FeeInvoice)
        assert inv.amount_due == Decimal("7500.00")

        payment = fee_repo.create_payment(
            db_session,
            fee_invoice_id=inv.id,
            provider="fakepay",
            provider_txn_id="txn123",
            amount=Decimal("7500.00"),
            status="success",
            idempotency_key="idem-1",
        )
        assert isinstance(payment, Payment)
        assert payment.fee_invoice_id == inv.id

        updated = fee_repo.mark_invoice_paid(db_session, inv)
        assert updated.status == "paid"

        receipt = fee_repo.create_receipt(
            db_session,
            payment_id=payment.id,
            receipt_no="R-001",
            pdf_path="/tmp/receipt.pdf",
        )
        assert isinstance(receipt, Receipt)
        assert receipt.receipt_no == "R-001"
