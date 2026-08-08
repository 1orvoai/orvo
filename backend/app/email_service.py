"""
Real SMTP email sending. Requires SMTP_HOST/SMTP_USER/SMTP_PASSWORD in .env.
If not configured, emails are logged to console instead of silently "faking" success —
this makes local development possible without an SMTP account while being transparent
that no real email was sent.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import settings


def is_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    if not is_configured():
        print(f"[ORVO][email:NOT SENT - SMTP not configured] to={to_email} subject={subject}\n{html_body}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls(context=context)
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[ORVO][email:ERROR] {e}")
        return False


def send_password_reset_email(to_email: str, reset_link: str):
    html = f"""
    <div style="font-family:Arial,sans-serif;background:#0b0e14;color:#e6e9ef;padding:32px">
      <h2 style="color:#3b82f6">ORVO Password Reset</h2>
      <p>We received a request to reset your ORVO account password.</p>
      <p><a href="{reset_link}" style="background:#3b82f6;color:#fff;padding:10px 20px;
      border-radius:6px;text-decoration:none">Reset Password</a></p>
      <p>This link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.
      If you did not request this, you can safely ignore this email.</p>
    </div>
    """
    return send_email(to_email, "Reset your ORVO password", html)
