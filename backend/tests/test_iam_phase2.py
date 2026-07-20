import pytest
import secrets
import hashlib
from datetime import datetime, timedelta
from app.services.auth import AuthService, validate_password_strength
from app.services.session import SessionService
from app.services.audit import AuditLogService
from app.core.events import EventPublisher
from app.db.models import User, UserSession, AuditLog
from sqlalchemy.exc import IntegrityError


class MockEventPublisher(EventPublisher):
    def __init__(self):
        self.events = []

    def publish(self, event_type: str, data: dict) -> None:
        self.events.append((event_type, data))


@pytest.fixture(autouse=True)
def configure_strict_passwords():
    from app.core.config import settings
    # Save original settings
    orig_len = settings.PASSWORD_MIN_LENGTH
    orig_upper = settings.PASSWORD_REQUIRE_UPPERCASE
    orig_lower = settings.PASSWORD_REQUIRE_LOWERCASE
    orig_num = settings.PASSWORD_REQUIRE_NUMBER
    orig_special = settings.PASSWORD_REQUIRE_SPECIAL

    # Set strict values for IAM tests
    settings.PASSWORD_MIN_LENGTH = 12
    settings.PASSWORD_REQUIRE_UPPERCASE = True
    settings.PASSWORD_REQUIRE_LOWERCASE = True
    settings.PASSWORD_REQUIRE_NUMBER = True
    settings.PASSWORD_REQUIRE_SPECIAL = True

    yield

    # Restore original settings
    settings.PASSWORD_MIN_LENGTH = orig_len
    settings.PASSWORD_REQUIRE_UPPERCASE = orig_upper
    settings.PASSWORD_REQUIRE_LOWERCASE = orig_lower
    settings.PASSWORD_REQUIRE_NUMBER = orig_num
    settings.PASSWORD_REQUIRE_SPECIAL = orig_special


def test_password_strength_validator():
    # Test short password
    ok, err = validate_password_strength("Short1!")
    assert not ok
    assert "at least 12 characters" in err

    # Test missing uppercase
    ok, err = validate_password_strength("lowercase123!")
    assert not ok
    assert "uppercase letter" in err

    # Test missing lowercase
    ok, err = validate_password_strength("UPPERCASE123!")
    assert not ok
    assert "lowercase letter" in err

    # Test missing number
    ok, err = validate_password_strength("NoNumbersHere!")
    assert not ok
    assert "digit" in err

    # Test missing special
    ok, err = validate_password_strength("NoSpecials1234")
    assert not ok
    assert "special character" in err

    # Test valid complex password
    ok, err = validate_password_strength("SecurePassword123!")
    assert ok
    assert err is None


def test_iam_registration_flow(db_session):
    publisher = MockEventPublisher()
    auth_service = AuthService(db_session, event_publisher=publisher)

    # Register user with weak password (fails)
    user, err = auth_service.register_user("weak@docmind.com", "weak", "Weak Pass")
    assert user is None
    assert "at least 12 characters" in err

    # Register successfully
    user, err = auth_service.register_user("iam_u1@docmind.com", "SecurePassword123!", "IAM User")
    assert err is None
    assert user is not None
    assert user.email == "iam_u1@docmind.com"
    assert user.is_verified is False  # EmailVerificationEnabled is True
    assert user.verification_token_hash is not None

    # Check that USER_REGISTERED event was published
    assert len(publisher.events) == 1
    assert publisher.events[0][0] == "USER_REGISTERED"
    assert publisher.events[0][1]["email"] == "iam_u1@docmind.com"
    assert publisher.events[0][1]["verification_token"] is not None


def test_iam_email_verification_flow(db_session):
    publisher = MockEventPublisher()
    auth_service = AuthService(db_session, event_publisher=publisher)

    # Register
    user, _ = auth_service.register_user("iam_u2@docmind.com", "SecurePassword123!", "IAM User 2")
    raw_token = publisher.events[0][1]["verification_token"]

    # Verify with invalid token
    success, err = auth_service.verify_email("invalid_token_123")
    assert not success
    assert "Invalid or expired" in err

    # Verify successfully
    success, err = auth_service.verify_email(raw_token)
    assert success
    assert err is None
    assert user.is_verified is True
    assert user.verification_token_hash is None  # One-time use: cleared

    # Check verified event
    assert publisher.events[1][0] == "EMAIL_VERIFIED"
    assert publisher.events[1][1]["user_id"] == user.id


def test_iam_login_lockout_flow(db_session):
    publisher = MockEventPublisher()
    auth_service = AuthService(db_session, event_publisher=publisher)

    email = "lockout@docmind.com"
    user, _ = auth_service.register_user(email, "SecurePassword123!", "Lockout User")
    # Verify email first so we can authenticate
    auth_service.verify_email(publisher.events[0][1]["verification_token"])
    publisher.events.clear()

    # Fail login 4 times
    for i in range(4):
        u, err = auth_service.authenticate_user(email, "wrong_password")
        assert u is None
        assert err == "Invalid email or password"
        assert user.login_attempts == i + 1

    # 5th failure triggers lockout
    u, err = auth_service.authenticate_user(email, "wrong_password")
    assert u is None
    assert "locked" in err.lower()
    assert user.login_attempts == 5
    assert user.locked_until is not None

    # Verify ACCOUNT_LOCKED event was published
    locked_events = [ev for ev in publisher.events if ev[0] == "ACCOUNT_LOCKED"]
    assert len(locked_events) >= 1

    # Attempt authenticating while locked (fails immediately)
    u, err = auth_service.authenticate_user(email, "SecurePassword123!")
    assert u is None
    assert "locked" in err.lower()


def test_iam_forgot_reset_password_flow(db_session):
    publisher = MockEventPublisher()
    auth_service = AuthService(db_session, event_publisher=publisher)

    email = "forgot@docmind.com"
    user, _ = auth_service.register_user(email, "SecurePassword123!", "Forgot User")
    auth_service.verify_email(publisher.events[0][1]["verification_token"])
    publisher.events.clear()

    # Forgot password blind notice (returns true even if non-existent, but internally runs only for real users)
    success, err = auth_service.forgot_password("nonexistent@docmind.com")
    assert success
    assert err is None
    assert len(publisher.events) == 0

    # Forgot password for real user
    success, err = auth_service.forgot_password(email)
    assert success
    assert err is None
    assert len(publisher.events) == 1
    assert publisher.events[0][0] == "PASSWORD_RESET_REQUESTED"
    raw_reset_token = publisher.events[0][1]["reset_token"]

    # Reset password with weak password (fails)
    success, err = auth_service.reset_password(raw_reset_token, "weak")
    assert not success
    assert "at least 12 characters" in err

    # Reset password successfully
    success, err = auth_service.reset_password(raw_reset_token, "NewSecurePassword123!")
    assert success
    assert err is None
    assert user.password_reset_token_hash is None
    assert user.login_attempts == 0
    assert user.locked_until is None

    # Check completion event
    assert publisher.events[1][0] == "PASSWORD_RESET_COMPLETED"


def test_iam_sessions_and_token_rotation(db_session):
    publisher = MockEventPublisher()
    auth_service = AuthService(db_session, event_publisher=publisher)
    session_service = SessionService(db_session)

    email = "sessions@docmind.com"
    user, _ = auth_service.register_user(email, "SecurePassword123!", "Sessions User")
    auth_service.verify_email(publisher.events[0][1]["verification_token"])
    publisher.events.clear()

    # Login
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ip = "192.168.1.50"
    data, err = auth_service.login_user(email, "SecurePassword123!", ip_address=ip, user_agent=user_agent)
    assert err is None
    assert data is not None
    
    refresh_token = data["refresh_token"]

    # Verify session tracking details parsed browser & OS
    active_sessions = session_service.list_active_sessions(user.id)
    assert len(active_sessions) == 1
    session = active_sessions[0]
    assert session.browser == "Chrome"
    assert session.operating_system == "Windows"
    assert session.device_name == "Desktop"
    assert session.ip_address == ip

    # Refresh token rotation
    rotate_data, err = auth_service.refresh_access_token(refresh_token, ip_address=ip, user_agent=user_agent)
    assert err is None
    assert rotate_data is not None
    new_refresh_token = rotate_data["refresh_token"]

    # Verify old session was revoked and new one was created (rotation)
    active_sessions_after = session_service.list_active_sessions(user.id)
    assert len(active_sessions_after) == 1
    assert active_sessions_after[0].refresh_token_jti != session.refresh_token_jti

    # Replay attack: try using the rotated old refresh token (must revoke all active sessions of this user)
    replay_data, err = auth_service.refresh_access_token(refresh_token, ip_address=ip, user_agent=user_agent)
    assert replay_data is None
    assert "revoked" in err.lower()

    # Verify all sessions are indeed revoked now
    assert len(session_service.list_active_sessions(user.id)) == 0


def test_audit_logs_service(db_session):
    audit_service = AuditLogService(db_session)

    log = audit_service.log_event(
        user_id=999,
        event_type="LOGIN_SUCCESS",
        request_id="req-111",
        ip_address="127.0.0.1",
        user_agent="MockClient",
        metadata={"status": "verified"}
    )
    assert log is not None
    assert log.event_type == "LOGIN_SUCCESS"
    assert log.request_id == "req-111"

    logs = audit_service.list_logs_for_user(999)
    assert len(logs) == 1
    assert logs[0].id == log.id
