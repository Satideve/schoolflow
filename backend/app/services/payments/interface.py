# backend/app/services/payments/interface.py
from typing import Protocol, Dict, Any

class PaymentGatewayInterface(Protocol):
    def create_order(self, amount_in_rupees: float, currency: str, receipt: str, notes: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Create a payment order and return provider-specific data needed for checkout."""
        ...

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify webhook authenticity (HMAC signature for Razorpay)."""
        ...
