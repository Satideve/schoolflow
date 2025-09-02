# backend/app/services/messaging/interface.py
from typing import Protocol, Dict, Any

class MessagingInterface(Protocol):
    def send_email(self, to_email: str, subject: str, body_html: str) -> Dict[str, Any]:
        ...
    def send_whatsapp(self, phone: str, message: str) -> Dict[str, Any]:
        ...
