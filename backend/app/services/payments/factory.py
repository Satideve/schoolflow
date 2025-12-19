# backend/app/services/payments/factory.py
"""
Payment gateway factory.

Chooses the correct payment provider based on settings.PROVIDER_MODE.
"""

from typing import TYPE_CHECKING
from app.core.config import settings
from app.services.payments.fake_adapter import FakePaymentAdapter

if TYPE_CHECKING:
    from app.services.payments.interface import PaymentGatewayInterface


def get_payment_gateway():
    """
    Return the configured payment gateway.

    PROVIDER_MODE values:
      - "fake"     → FakePaymentAdapter (default, local/dev)
      - "razorpay" → RazorpayAdapter (explicit opt-in only)
    """
    mode = (settings.provider_mode or "fake").lower()

    if mode == "razorpay":
        # ⚠ Import ONLY when needed (prevents startup crashes)
        from app.services.payments.razorpay_adapter import RazorpayAdapter
        return RazorpayAdapter()

    # Default / safe fallback
    return FakePaymentAdapter()
