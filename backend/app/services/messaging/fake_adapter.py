# backend/app/services/messaging/fake_adapter.py
"""
Fake messaging adapter that logs messages to stdout for dev.
"""
from app.services.messaging.interface import MessagingInterface
from app.core.logging import get_logger

logger = get_logger("messaging", request_id=None)

class FakeMessagingAdapter(MessagingInterface):
    def send_email(self, to_email: str, subject: str, body_html: str):
        logger.info(f"[FakeEmail] to={to_email} subject={subject}")
        # return a fake message ID
        return {"message_id": "fake-msg-" + to_email}

    def send_whatsapp(self, phone: str, message: str):
        logger.info(f"[FakeWhatsApp] to={phone} message={message}")
        return {"status": "sent"}
