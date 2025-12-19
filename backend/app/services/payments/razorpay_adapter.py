# backend/app/services/payments/razorpay_adapter.py

"""
Razorpay payment adapter (stub).

This file is intentionally minimal.
Actual Razorpay integration will be added later.
"""

from app.services.payments.interface import PaymentGatewayInterface


class RazorpayAdapter(PaymentGatewayInterface):
    def create_order(self, *args, **kwargs):
        raise NotImplementedError("Razorpay is not enabled yet")

    def verify_webhook(self, *args, **kwargs):
        raise NotImplementedError("Razorpay is not enabled yet")
