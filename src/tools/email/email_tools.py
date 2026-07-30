import smtplib
from email.message import EmailMessage
from typing import Dict, Optional

from src.config import settings


class EmailTool:
    """Creates drafts and sends SMTP messages when configured."""

    def draft(self, to_email: str, subject: str, body: str) -> Dict[str, str]:
        return {
            "to": to_email,
            "subject": subject,
            "body": body,
            "status": "drafted",
        }

    def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        dry_run: bool = True,
    ) -> Dict[str, str]:
        draft = self.draft(to_email, subject, body)
        if dry_run:
            draft["status"] = "dry_run"
            return draft

        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            raise EnvironmentError("SMTP settings are incomplete")

        message = EmailMessage()
        message["From"] = from_email or settings.SMTP_FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)

        return {"to": to_email, "subject": subject, "status": "sent"}
