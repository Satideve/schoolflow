# backend/app/services/payments/fake_adapter.py
"""
Fake payment adapter for local testing. Returns deterministic test objects.
"""
from app.services.payments.interface import PaymentGatewayInterface
import uuid
from typing import Dict, Any

class FakePaymentAdapter(PaymentGatewayInterface):
    def create_order(self, amount_in_rupees: float, currency: str = "INR", receipt: str = "", notes: Dict[str, Any] | None = None) -> Dict[str, Any]:
        order_id = f"fake_order_{uuid.uuid4().hex}"
        return {
            "id": order_id,
            "amount": int(amount_in_rupees * 100),  # paise
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "notes": notes or {},
        }

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        # Fake adapter always accepts a signature "fake-signature" for test harness
        return signature == "fake-signature"
