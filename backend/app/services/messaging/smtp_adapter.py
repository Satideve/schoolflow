# backend/app/services/messaging/smtp_adapter.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

from app.core.config import settings
from app.services.messaging.interface import MessagingInterface
from email.mime.application import MIMEApplication



class SMTPMessagingAdapter(MessagingInterface):
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        attachment: bytes | None = None,
        attachment_filename: str | None = None,
    ) -> Dict[str, Any]:
        # -------------------------------
        # Mode-authoritative SMTP safety
        # -------------------------------
        if settings.smtp_mode == "prod":
            # Production: real SMTP is REQUIRED
            if not settings.smtp_host:
                raise RuntimeError(
                    "SMTP_MODE=prod but SMTP_HOST is not configured"
                )

            if not settings.smtp_user or not settings.smtp_password:
                raise RuntimeError(
                    "SMTP_MODE=prod but SMTP_USER / SMTP_PASSWORD are not configured"
                )

        else:
            # Dev mode: NEVER allow real SMTP credentials
            # Force MailHog-style behavior
            if settings.smtp_host not in ("localhost", "127.0.0.1"):
                raise RuntimeError(
                    "SMTP_MODE=dev but SMTP_HOST is not localhost"
                )


            
        msg = MIMEMultipart("mixed")
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg["Subject"] = subject

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(body_html, "html"))
        msg.attach(alt)


        if attachment and attachment_filename:
            part = MIMEApplication(attachment)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{attachment_filename}"',
            )
            msg.attach(part)

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:

                if settings.smtp_mode == "prod":
                    server.starttls()
                    server.login(
                        settings.smtp_user,
                        settings.smtp_password,
                    )

                # dev mode intentionally skips TLS + auth

                server.sendmail(
                    from_addr=settings.smtp_from,
                    to_addrs=[to_email],
                    msg=msg.as_string(),
                )

            return {"status": "sent", "to": to_email}

        except Exception as exc:
            return {"status": "error", "error": str(exc)}
