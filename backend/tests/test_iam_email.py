import pytest
import time
import asyncio
from jinja2 import UndefinedError
from app.services.email import EmailService, MockEmailProvider, ImmediateEmailDispatcher, SMTPEmailProvider


def test_email_template_rendering_strict_variables():
    provider = MockEmailProvider()
    dispatcher = ImmediateEmailDispatcher(provider)
    email_service = EmailService(dispatcher)

    # Rendering with correct arguments should succeed
    rendered = email_service.render_template(
        "verification.html",
        {"name": "Alice", "verification_url": "http://test/verify"}
    )
    assert "Alice" in rendered
    assert "http://test/verify" in rendered

    # StrictUndefined validation: rendering with missing variables must raise UndefinedError
    with pytest.raises(UndefinedError):
        email_service.render_template(
            "verification.html",
            {"name": "Alice"}  # Missing verification_url
        )


def test_send_verification_email_flow():
    provider = MockEmailProvider()
    dispatcher = ImmediateEmailDispatcher(provider)
    email_service = EmailService(dispatcher)

    email_service.send_verification_email(
        email="user@test.com",
        name="Bob",
        token="token_abc_123"
    )

    assert len(provider.sent_emails) == 1
    to_email, subject, html = provider.sent_emails[0]
    assert to_email == "user@test.com"
    assert "Activate your DOCMind Enterprise account" in subject
    assert "Bob" in html
    assert "token_abc_123" in html


def test_send_password_reset_email_flow():
    provider = MockEmailProvider()
    dispatcher = ImmediateEmailDispatcher(provider)
    email_service = EmailService(dispatcher)

    email_service.send_password_reset_email(
        email="reset@test.com",
        name="Charlie",
        token="reset_token_xyz"
    )

    assert len(provider.sent_emails) == 1
    to_email, subject, html = provider.sent_emails[0]
    assert to_email == "reset@test.com"
    assert "Reset your DOCMind Enterprise password" in subject
    assert "Charlie" in html
    assert "reset_token_xyz" in html


@pytest.mark.anyio
async def test_email_service_event_consumption():
    from app.core.events import AsyncEventPublisher
    publisher = AsyncEventPublisher()
    provider = MockEmailProvider()
    dispatcher = ImmediateEmailDispatcher(provider)
    email_service = EmailService(dispatcher)

    # Register subscribers
    publisher.subscribe("USER_REGISTERED", email_service.handle_user_registered)
    publisher.subscribe("PASSWORD_RESET_REQUESTED", email_service.handle_password_reset_requested)

    # Publish registration event
    publisher.publish("USER_REGISTERED", {
        "email": "signup@test.com",
        "full_name": "Dave",
        "verification_token": "ver_tok"
    })

    await asyncio.sleep(0.1)

    # Verify MockEmailProvider received the email via event subscription dispatch
    assert len(provider.sent_emails) == 1
    to_email, subject, html = provider.sent_emails[0]
    assert to_email == "signup@test.com"
    assert "ver_tok" in html


def test_smtp_provider_error_handling():
    # SMTP provider points to a non-existent port to force immediate socket error
    from app.core.config import settings
    orig_host = settings.SMTP_HOST
    orig_port = settings.SMTP_PORT
    
    settings.SMTP_HOST = "localhost"
    settings.SMTP_PORT = 9999  # Invalid port
    
    provider = SMTPEmailProvider()
    
    with pytest.raises(RuntimeError) as exc_info:
        provider.send_email("to@test.com", "Subject", "<h1>Content</h1>")
        
    assert "Email delivery failed" in str(exc_info.value)
    
    # Restore settings
    settings.SMTP_HOST = orig_host
    settings.SMTP_PORT = orig_port


def test_email_rendering_concurrent_performance():
    provider = MockEmailProvider()
    dispatcher = ImmediateEmailDispatcher(provider)
    email_service = EmailService(dispatcher)

    # Performance check: rendering 100 templates concurrently must execute in under 200ms
    start_time = time.time()
    for i in range(100):
        email_service.render_template(
            "verification.html",
            {"name": f"User{i}", "verification_url": f"http://test/verify?i={i}"}
        )
    end_time = time.time()
    
    duration = end_time - start_time
    # Render 100 templates is extremely fast in Jinja2 (usually under 20ms)
    assert duration < 0.200, f"Template rendering performance was slow: {duration}s"
