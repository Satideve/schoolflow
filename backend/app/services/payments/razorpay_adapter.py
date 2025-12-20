# backend/app/services/payments/razorpay_adapter.py

"""
Razorpay payment adapter (stub).

This file is intentionally minimal.
Actual Razorpay integration will be added later.
"""

from app.services.payments.interface import PaymentGatewayInterface


class RazorpayAdapter(PaymentGatewayInterface):
    def _get_client(self):
        """
        Lazily construct Razorpay client.

        IMPORTANT:
        - Import happens at runtime (not module import)
        - No env vars read yet
        - No network calls
        - Safe even if Razorpay SDK is not installed until used
        """
        import razorpay  # local import by design

        # Credentials will be wired in a later step
        # This is intentionally incomplete and unused for now
        return razorpay.Client(auth=("__unused__", "__unused__"))

    def create_order(self, *args, **kwargs):
        raise NotImplementedError("Razorpay is not enabled yet")

    def verify_webhook(self, *args, **kwargs):
        raise NotImplementedError("Razorpay is not enabled yet")
