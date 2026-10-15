import smtplib
from email.message import EmailMessage
from typing import Dict, Any, Optional
from ..config import settings

class EmailService:
    def __init__(self):
        self.last_sent_emails = [] # in-memory history for dev inspection

    def _send_smtp(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            return False

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email
            msg.set_content(text_content)
            msg.add_alternative(html_content, subtype="html")

            if settings.SMTP_TLS:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    if settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    if settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            return True
        except Exception as e:
            print(f"[DANFEZ EMAIL] SMTP delivery error: {e}")
            return False

    def send_password_reset_email(self, to_email: str, user_name: str, token: str) -> Dict[str, Any]:
        reset_url = f"{settings.APP_URL}/reset-password.html?token={token}"
        subject = "DANFEZ TECH HOUSE — Password Reset Request"
        
        text_content = f"""
Hello {user_name},

We received a request to reset your password for your Danfez Lift Control account.
Click the link below or copy it into your browser to reset your password:

{reset_url}

This link is single-use and will expire in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.
If you did not make this request, you can safely ignore this email.

— DANFEZ TECH HOUSE Security Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, sans-serif; background-color: #F4F7FB; color: #07162B; margin: 0; padding: 20px; }}
    .card {{ background: #FFFFFF; max-width: 520px; margin: 0 auto; padding: 30px; border-radius: 12px; border: 1px solid #E2E8F0; }}
    .btn {{ background-color: #168BFF; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; margin: 20px 0; }}
    .footer {{ font-size: 12px; color: #64748B; margin-top: 25px; border-top: 1px solid #E2E8F0; padding-top: 15px; }}
  </style>
</head>
<body>
  <div class="card">
    <h2 style="color: #07162B; margin-top: 0;">DANFEZ TECH HOUSE</h2>
    <h4 style="color: #168BFF; margin-top: 0;">Password Reset Request</h4>
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>We received a request to reset your password for your <strong>Danfez Lift Control</strong> account.</p>
    <div style="text-align: center;">
      <a href="{reset_url}" class="btn">Reset My Password</a>
    </div>
    <p style="font-size: 13px; color: #64748B;">This link is single-use and expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes. If you did not request this, please ignore this email.</p>
    <div class="footer">
      DANFEZ TECH HOUSE &bull; Intelligent Elevator Monitoring & Maintenance &bull; &copy; 2026
    </div>
  </div>
</body>
</html>
"""
        smtp_success = self._send_smtp(to_email, subject, html_content, text_content)
        
        # Log to terminal for easy developer inspection
        print(f"[DANFEZ EMAIL] Password Reset link generated for {to_email}: {reset_url}")
        
        email_record = {
            "type": "PASSWORD_RESET",
            "to": to_email,
            "reset_url": reset_url,
            "token": token,
            "smtp_sent": smtp_success
        }
        self.last_sent_emails.append(email_record)
        return email_record

    def send_verification_email(self, to_email: str, user_name: str, token: str) -> Dict[str, Any]:
        verify_url = f"{settings.APP_URL}/verify-email.html?token={token}"
        subject = "DANFEZ TECH HOUSE — Verify Your Email Address"

        text_content = f"""
Hello {user_name},

Welcome to Danfez Lift Control. Please verify your email address by opening the following link:

{verify_url}

— DANFEZ TECH HOUSE Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, sans-serif; background-color: #F4F7FB; color: #07162B; margin: 0; padding: 20px; }}
    .card {{ background: #FFFFFF; max-width: 520px; margin: 0 auto; padding: 30px; border-radius: 12px; border: 1px solid #E2E8F0; }}
    .btn {{ background-color: #18A874; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; margin: 20px 0; }}
    .footer {{ font-size: 12px; color: #64748B; margin-top: 25px; border-top: 1px solid #E2E8F0; padding-top: 15px; }}
  </style>
</head>
<body>
  <div class="card">
    <h2 style="color: #07162B; margin-top: 0;">DANFEZ TECH HOUSE</h2>
    <h4 style="color: #18A874; margin-top: 0;">Verify Your Email Address</h4>
    <p>Hello <strong>{user_name}</strong>,</p>
    <p>Thank you for registering on <strong>Danfez Lift Control</strong>. Please confirm your email address to complete verification:</p>
    <div style="text-align: center;">
      <a href="{verify_url}" class="btn">Verify Email Address</a>
    </div>
    <div class="footer">
      DANFEZ TECH HOUSE &bull; Intelligent Elevator Monitoring & Maintenance &bull; &copy; 2026
    </div>
  </div>
</body>
</html>
"""
        smtp_success = self._send_smtp(to_email, subject, html_content, text_content)
        print(f"[DANFEZ EMAIL] Verification link generated for {to_email}: {verify_url}")
        
        email_record = {
            "type": "EMAIL_VERIFICATION",
            "to": to_email,
            "verify_url": verify_url,
            "token": token,
            "smtp_sent": smtp_success
        }
        self.last_sent_emails.append(email_record)
        return email_record

email_service = EmailService()
