import os
import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined
from app.core.config import settings

logger = logging.getLogger("app.email")


# 1. Email Provider Abstraction (Internal)
class EmailProvider(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        """Abstract method to deliver HTML email content to target recipient."""
        pass


class MockEmailProvider(EmailProvider):
    def __init__(self):
        self.sent_emails = []

    def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        self.sent_emails.append((to_email, subject, html_content))
        # Secure logging: Log only metadata, never raw URLs, body secrets, or tokens
        logger.info(
            f"[MOCK EMAIL] Sent to: {to_email} | Subject: {subject} | "
            f"HTML Body Size: {len(html_content)} bytes"
        )


class EmailDeliveryException(RuntimeError):
    """Custom exception raised when email delivery fails."""
    pass


class SMTPEmailProvider(EmailProvider):
    def __init__(self):
        # Validate critical configurations at startup
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.sender = settings.SMTP_FROM

        if not self.host:
            raise ValueError("SMTP_HOST configuration is missing.")
        if not self.port or not isinstance(self.port, int) or self.port <= 0:
            raise ValueError(f"SMTP_PORT must be a positive integer, got: {self.port}")
        if not self.sender:
            raise ValueError("SMTP_FROM configuration is missing.")

    def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))

        max_retries = 3
        timeout_seconds = 10.0

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempting SMTP email delivery to {to_email} (Attempt {attempt}/{max_retries})...")
                
                # Implicit SSL for Port 465, explicit STARTTLS for standard ports
                if self.port == 465:
                    server = smtplib.SMTP_SSL(self.host, self.port, timeout=timeout_seconds)
                else:
                    server = smtplib.SMTP(self.host, self.port, timeout=timeout_seconds)

                with server:
                    # Explicit protocol negotiation (EHLO)
                    server.ehlo()

                    # Port 587 or 25 upgrades via STARTTLS
                    if self.port != 465:
                        if server.has_ext("STARTTLS"):
                            server.starttls()
                            server.ehlo()  # Re-send EHLO to negotiate authenticated commands
                        else:
                            logger.warning("SMTP server does not support STARTTLS, continuing in plaintext.")

                    # Authentication
                    if self.username and self.password:
                        server.login(self.username, self.password)

                    server.sendmail(self.sender, [to_email], msg.as_string())
                
                logger.info(f"SMTP email sent successfully to {to_email} (Size: {len(html_content)} bytes)")
                return  # Success, exit the retry loop
                
            except Exception as e:
                # Exponential backoff: 1s, 2s, 4s delay
                backoff_delay = 2.0 ** (attempt - 1)
                logger.warning(
                    f"SMTP delivery attempt {attempt} failed for {to_email}: {str(e)}"
                )
                if attempt == max_retries:
                    logger.error(
                        f"Failed to send SMTP email to {to_email} after {max_retries} attempts: {str(e)}", 
                        exc_info=True
                    )
                    raise EmailDeliveryException(f"Email delivery failed: SMTP delivery failed after {max_retries} attempts: {str(e)}")
                import time
                time.sleep(backoff_delay)


# 2. Email Dispatcher Abstraction (Decouples delivery scheduler/queue)
class EmailDispatcher(ABC):
    @abstractmethod
    def dispatch(self, to_email: str, subject: str, html_content: str) -> None:
        """Dispatch email asynchronously or immediately to provider."""
        pass


class ImmediateEmailDispatcher(EmailDispatcher):
    def __init__(self, provider: EmailProvider):
        self.provider = provider

    def dispatch(self, to_email: str, subject: str, html_content: str) -> None:
        # Immediate sync delegation (asynchronous behavior is handled by loop task/event bus layer)
        self.provider.send_email(to_email, subject, html_content)


# 3. EmailService (Unified Public Interface)
class EmailService:
    def __init__(self, dispatcher: EmailDispatcher):
        self.dispatcher = dispatcher
        
        # Configure Jinja2 environment with autoescape and strict undefined values
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            undefined=StrictUndefined
        )

    def render_template(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)

    def send_verification_email(self, email: str, name: str, token: str) -> None:
        base_url = settings.FRONTEND_URL.rstrip("/")
        verification_url = f"{base_url}/auth/verify-email?token={token}"
        html_content = self.render_template(
            "verification.html",
            {
                "name": name or email,
                "verification_url": verification_url
            }
        )
        self.dispatcher.dispatch(
            to_email=email,
            subject="Activate your DOCMind Enterprise account",
            html_content=html_content
        )

    def send_password_reset_email(self, email: str, name: str, token: str) -> None:
        base_url = settings.FRONTEND_URL.rstrip("/")
        reset_url = f"{base_url}/auth/reset-password?token={token}"
        html_content = self.render_template(
            "password_reset.html",
            {
                "name": name or email,
                "reset_url": reset_url
            }
        )
        self.dispatcher.dispatch(
            to_email=email,
            subject="Reset your DOCMind Enterprise password",
            html_content=html_content
        )

    # Decoupled Event Listeners
    def handle_user_registered(self, event) -> None:
        payload = event.payload
        verification_token = payload.get("verification_token")
        if verification_token:
            self.send_verification_email(
                email=payload["email"],
                name=payload.get("full_name") or payload["email"],
                token=verification_token
            )

    def handle_password_reset_requested(self, event) -> None:
        payload = event.payload
        reset_token = payload.get("reset_token")
        if reset_token:
            self.send_password_reset_email(
                email=payload["email"],
                name=payload.get("full_name") or payload["email"],
                token=reset_token
            )
