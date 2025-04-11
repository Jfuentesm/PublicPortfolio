# app/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from core.config import settings
from core.logging_config import get_logger

logger = get_logger("vendor_classification.email_service")

# NOTE: For this service to work, you need to install fastapi-mail or handle SMTP directly.
# Example using standard smtplib (requires SMTP server details in config)
# For a real app, consider libraries like fastapi-mail for better integration and features (e.g., templates).

# --- SMTP Configuration (Ensure these are set in your .env or config.py) ---
SMTP_HOST: Optional[str] = getattr(settings, "SMTP_HOST", None)
SMTP_PORT: int = getattr(settings, "SMTP_PORT", 587) # Default TLS port
SMTP_USER: Optional[str] = getattr(settings, "SMTP_USER", None)
SMTP_PASSWORD: Optional[str] = getattr(settings, "SMTP_PASSWORD", None)
SMTP_TLS: bool = getattr(settings, "SMTP_TLS", True) # Use TLS by default
EMAIL_FROM: Optional[str] = getattr(settings, "EMAIL_FROM", None) # Sender email address
FRONTEND_URL: str = getattr(settings, "FRONTEND_URL", "http://localhost:8080") # Base URL for reset link

def is_email_configured() -> bool:
    """Check if essential SMTP settings are configured."""
    configured = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD and EMAIL_FROM)
    if not configured:
        logger.warning("Email service is not configured. SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM must be set in settings.")
    return configured

def send_email(to_email: str, subject: str, body_html: str) -> bool:
    """Sends an email using configured SMTP settings."""
    if not is_email_configured():
        logger.error("Cannot send email: Email service not configured.")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = to_email

    # Create the plain-text and HTML version of your message
    # For simplicity, we'll just use the HTML body here.
    # Consider adding a plain text alternative for email clients that don't support HTML.
    # text = "Please enable HTML viewing to see this message."
    # part1 = MIMEText(text, "plain")
    part2 = MIMEText(body_html, "html")

    # message.attach(part1)
    message.attach(part2)

    try:
        logger.info(f"Attempting to send email", extra={"to_email": to_email, "subject": subject, "smtp_host": SMTP_HOST, "smtp_port": SMTP_PORT})
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_TLS:
                server.starttls() # Secure the connection
            server.login(str(SMTP_USER), str(SMTP_PASSWORD))
            server.sendmail(str(EMAIL_FROM), to_email, message.as_string())
            logger.info(f"Email sent successfully", extra={"to_email": to_email, "subject": subject})
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Error. Check SMTP_USER and SMTP_PASSWORD.", exc_info=False)
        return False
    except smtplib.SMTPConnectError:
         logger.error(f"SMTP Connection Error. Could not connect to {SMTP_HOST}:{SMTP_PORT}.", exc_info=False)
         return False
    except smtplib.SMTPServerDisconnected:
         logger.error("SMTP Server Disconnected unexpectedly.", exc_info=False)
         return False
    except Exception as e:
        logger.error(f"Failed to send email", exc_info=True, extra={"to_email": to_email, "subject": subject, "error": str(e)})
        return False

def send_password_reset_email(email_to: str, username: str, token: str):
    """Sends the password reset email or logs the link if email is not configured."""
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password Reset Request"
    # IMPORTANT: Adjust the frontend URL path as needed
    reset_url = f"{FRONTEND_URL}/reset-password/{token}" # Ensure this matches your frontend route

    body_html = f"""
    <html>
    <body>
        <p>Hello {username},</p>
        <p>You requested a password reset for your account on {project_name}.</p>
        <p>Click the link below to set a new password:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>Thanks,</p>
        <p>The {project_name} Team</p>
    </body>
    </html>
    """

    if is_email_configured():
        send_email(email_to, subject, body_html)
    else:
        # --- Fallback for MVP/Testing: Log the reset link ---
        logger.warning("Email service not configured. Logging password reset link instead of sending email.")
        print("-" * 80)
        print(f"PASSWORD RESET SIMULATION:")
        print(f"To: {email_to}")
        print(f"Subject: {subject}")
        print(f"Username: {username}")
        print(f"Reset URL: {reset_url}")
        print("-" * 80)
        # --- End Fallback ---

# Example Usage (for testing):
# if __name__ == "__main__":
#     # Make sure settings are loaded correctly if running standalone
#     # You might need to adjust sys.path or load .env
#     from dotenv import load_dotenv
#     load_dotenv()
#     from core.config import settings # Re-import after load_dotenv
#
#     # Update placeholders with actual values if needed for testing
#     SMTP_HOST = getattr(settings, "SMTP_HOST", "smtp.example.com")
#     SMTP_PORT = getattr(settings, "SMTP_PORT", 587)
#     SMTP_USER = getattr(settings, "SMTP_USER", "user@example.com")
#     SMTP_PASSWORD = getattr(settings, "SMTP_PASSWORD", "password")
#     EMAIL_FROM = getattr(settings, "EMAIL_FROM", "noreply@example.com")
#     FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:8080")
#
#     print(f"Email Configured: {is_email_configured()}")
#     if is_email_configured():
#          send_password_reset_email("test@example.com", "TestUser", "dummytoken12345")
#     else:
#          print("Run simulation:")
#          send_password_reset_email("test@example.com", "TestUser", "dummytoken12345")