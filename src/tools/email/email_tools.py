import smtplib
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Dict, List, Optional

from src.config import settings


class EmailTool:
    """Creates drafts and sends SMTP messages when configured."""

    def draft(
        self,
        to_email: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        result = {
            "to": to_email,
            "subject": subject,
            "body": body,
            "status": "drafted",
        }
        if cc:
            result["cc"] = cc
        if bcc:
            result["bcc"] = bcc
        if attachments:
            result["attachments"] = attachments
        return result

    def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        dry_run: bool = True,
        cc: str = "",
        bcc: str = "",
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        draft = self.draft(to_email, subject, body, cc, bcc, attachments)
        if dry_run:
            draft["status"] = "dry_run"
            return draft

        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            raise EnvironmentError("SMTP settings are incomplete")

        message = EmailMessage()
        message["From"] = from_email or settings.SMTP_FROM_EMAIL
        message["To"] = to_email
        if cc:
            message["Cc"] = cc
        if bcc:
            message["Bcc"] = bcc
        message["Subject"] = subject
        message.set_content(body)

        if attachments:
            for attachment_path in attachments:
                path = Path(attachment_path)
                if path.exists():
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=path.name)
                    part["Content-Disposition"] = f'attachment; filename="{path.name}"'
                    message.attach(part)

        recipients = [to_email]
        if cc:
            recipients.extend([e.strip() for e in cc.split(",")])
        if bcc:
            recipients.extend([e.strip() for e in bcc.split(",")])

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message, to_addrs=recipients)

        return {"to": to_email, "subject": subject, "status": "sent", "recipients": recipients}