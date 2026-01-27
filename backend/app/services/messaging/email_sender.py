# backend/app/services/messaging/email_sender.py

from typing import Dict, Any
from email.mime.application import MIMEApplication
from app.services.messaging import get_messaging_service


def send_document_email(
    *,
    to_email: str,
    subject: str,
    body_html: str,
    attachment: bytes | None = None,
    attachment_filename: str | None = None,
) -> Dict[str, Any]:

    """
    Send an email containing an HTML body.
    Attachments and PDFs will be layered later.
    """
    messaging = get_messaging_service()
    return messaging.send_email(
        to_email=to_email,
        subject=subject,
        body_html=body_html,
        attachment=attachment,
        attachment_filename=attachment_filename,
    )