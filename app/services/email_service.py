from email.message import EmailMessage

import aiosmtplib
from pydantic import EmailStr

from app.core.config import settings


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.email_user = settings.EMAIL_USER
        self.email_password = settings.EMAIL_PASSWORD


    async def send_email(self, to: EmailStr, subject: str, content: str):
        message = EmailMessage()
        message["FROM"] = self.email_user
        message["TO"] = to
        message["Subject"] = subject
        message.set_content(content)

        await aiosmtplib.send(
            message,
            hostname=self.smtp_host,
            port=self.smtp_port,
            start_tls=True,
            username=self.email_user,
            password=self.email_password
        )