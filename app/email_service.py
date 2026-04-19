from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import NamedTuple
from dotenv import load_dotenv

load_dotenv()
class SMTPSettings(NamedTuple):
    host: str
    port: int
    user: str | None
    password: str | None
    from_addr: str
    use_tls: bool


def load_smtp_settings() -> SMTPSettings | None:
    host = os.getenv("SMTP_HOST", "").strip()
    from_addr = os.getenv("SMTP_FROM", "").strip()
    if not host or not from_addr:
        return None

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip() or None
    password = os.getenv("SMTP_PASSWORD", "").strip() or None
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
    

    return SMTPSettings(
        host=host,
        port=port,
        user=user,
        password=password,
        from_addr=from_addr,
        use_tls=use_tls,
    )


def send_email_smtp(
    to_addr: str,
    subject: str,
    body: str,
    settings: SMTPSettings,
) -> None:
    print("🔌 Connecting to SMTP server...")
    print(f"📤 Preparing to send email to: {to_addr}")
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = settings.from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings.host, settings.port, timeout=30) as server:
            print("✅ Connected to SMTP")

            if settings.use_tls:
                print("🔐 Starting TLS...")
                server.starttls()

            if settings.user and settings.password:
                print(f"🔑 Logging in as: {settings.user}")
                server.login(settings.user, settings.password)

            print("📨 Sending email...")
            server.sendmail(settings.from_addr, [to_addr], msg.as_string())

            print("🎉 Email sent successfully (accepted by SMTP server)")

    except Exception as e:
        print("❌ ERROR while sending email:", str(e))
        raise
