# backend/app/services/messaging/__init__.py

from app.services.messaging.smtp_adapter import SMTPMessagingAdapter
from app.services.messaging.interface import MessagingInterface


def get_messaging_service() -> MessagingInterface:
    return SMTPMessagingAdapter()
