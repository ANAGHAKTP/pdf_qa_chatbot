import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.repositories.user import UserRepository
from app.repositories.session import SessionRepository
from app.db.models import User, UserSession
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.events import EventPublisher


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long."
        
    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
        
    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
        
    if settings.PASSWORD_REQUIRE_NUMBER and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
        
    if settings.PASSWORD_REQUIRE_SPECIAL:
        import string
        special_chars = set(string.punctuation)
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character."
            
    return True, None


def parse_browser(user_agent: Optional[str]) -> str:
    if not user_agent:
        return "Unknown"
    ua = user_agent.lower()
    if "edg" in ua:
        return "Edge"
    elif "chrome" in ua:
        return "Chrome"
    elif "firefox" in ua:
        return "Firefox"
    elif "safari" in ua:
        return "Safari"
    return "Browser"


def parse_os(user_agent: Optional[str]) -> str:
    if not user_agent:
        return "Unknown"
    ua = user_agent.lower()
    if "windows" in ua:
        return "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        return "macOS"
    elif "linux" in ua:
        return "Linux"
    elif "iphone" in ua or "ipad" in ua:
        return "iOS"
    elif "android" in ua:
        return "Android"
    return "OS"


def parse_device(user_agent: Optional[str]) -> str:
    if not user_agent:
        return "Unknown"
    ua = user_agent.lower()
    if "mobi" in ua or "iphone" in ua or "android" in ua:
        return "Mobile"
    return "Desktop"


class AuthService:
    def __init__(self, db: Session, event_publisher: Optional[EventPublisher] = None):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.event_publisher = event_publisher

    def register_user(self, email: str, password_plain: str, full_name: Optional[str] = None) -> Tuple[Optional[User], Optional[str]]:
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            return None, "Email already registered"
        
        # Enforce configurable password complexity policies
        is_valid, err_msg = validate_password_strength(password_plain)
        if not is_valid:
            return None, err_msg
            
        user_count = self.user_repo.count_users()
        role = "ADMIN" if user_count == 0 else "USER"
        is_admin = (role == "ADMIN")
        
        # Initialize verification token if configured
        verification_token = None
        verification_token_hash = None
        verification_token_expiry = None
        is_verified = True
        
        if settings.EMAIL_VERIFICATION_ENABLED:
            verification_token = secrets.token_urlsafe(32)
            verification_token_hash = hashlib.sha256(verification_token.encode()).hexdigest()
            verification_token_expiry = datetime.utcnow() + timedelta(hours=24)
            is_verified = False

        hashed_password = get_password_hash(password_plain)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_admin=is_admin,
            is_active=True,
            role=role,
            is_verified=is_verified,
            verification_token_hash=verification_token_hash,
            verification_token_expiry=verification_token_expiry,
            login_attempts=0
        )
        self.user_repo.save(user)

        if self.event_publisher:
            self.event_publisher.publish("USER_REGISTERED", {
                "user_id": user.id,
                "email": user.email,
                "verification_token": verification_token
            })

        return user, None

    def authenticate_user(self, email: str, password_plain: str) -> Tuple[Optional[User], Optional[str]]:
        # Acquire row level lock to prevent concurrent brute force attempts
        user = self.user_repo.get_by_email_with_lock(email)
        if not user:
            return None, "Invalid email or password"

        if user.locked_until and user.locked_until > datetime.utcnow():
            if self.event_publisher:
                self.event_publisher.publish("ACCOUNT_LOCKED", {"user_id": user.id, "email": user.email})
            return None, "Account is locked. Try again later."

        if not user.is_active:
            return None, "User account is disabled"

        if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
            return None, "Email address is not verified. Please check your inbox."

        if not verify_password(password_plain, user.hashed_password):
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                self.user_repo.save(user)
                if self.event_publisher:
                    self.event_publisher.publish("ACCOUNT_LOCKED", {"user_id": user.id, "email": user.email})
                return None, "Account is locked. Try again later."
                
            self.user_repo.save(user)
            if self.event_publisher:
                self.event_publisher.publish("LOGIN_FAILED", {"user_id": user.id, "email": user.email})
            return None, "Invalid email or password"

        user.login_attempts = 0
        user.locked_until = None
        self.user_repo.save(user)
        return user, None

    def login_user(self, email: str, password_plain: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[Optional[dict], Optional[str]]:
        user, err = self.authenticate_user(email, password_plain)
        if err:
            return None, err

        jti = str(uuid.uuid4())
        access_token = create_access_token(subject=user.id, role=user.role, jti=jti)
        refresh_token = create_refresh_token(subject=user.id, jti=jti)

        session = UserSession(
            user_id=user.id,
            refresh_token_jti=jti,
            status="ACTIVE",
            device_name=parse_device(user_agent),
            browser=parse_browser(user_agent),
            operating_system=parse_os(user_agent),
            ip_address=ip_address,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            last_activity=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        self.session_repo.create(session)

        if self.event_publisher:
            self.event_publisher.publish("LOGIN_SUCCESS", {"user_id": user.id, "email": user.email})
            self.event_publisher.publish("SESSION_CREATED", {"user_id": user.id, "session_id": session.id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin,
                "role": user.role
            }
        }, None

    def refresh_access_token(self, refresh_token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[Optional[dict], Optional[str]]:
        payload = decode_token(refresh_token, is_refresh=True)
        if not payload or payload.get("type") != "refresh":
            return None, "Invalid refresh token"

        jti = payload.get("jti")
        user_id_str = payload.get("sub")
        if not jti or not user_id_str:
            return None, "Invalid refresh token payload"

        try:
            user_id = int(user_id_str)
        except ValueError:
            return None, "Invalid user ID in token"

        session = self.session_repo.get_by_jti(jti)
        if not session or session.status != "ACTIVE":
            # Token Reuse/Replay Alert: Revoke all user sessions for safety
            self.session_repo.revoke_all_for_user(user_id)
            return None, "Session is invalid or revoked"

        if session.expires_at < datetime.utcnow():
            session.status = "EXPIRED"
            self.session_repo.save(session)
            return None, "Session has expired"

        # Verify inactivity window
        inactivity_limit = timedelta(minutes=settings.SESSION_INACTIVITY_TIMEOUT_MINUTES)
        if datetime.utcnow() - session.last_activity > inactivity_limit:
            session.status = "EXPIRED"
            self.session_repo.save(session)
            return None, "Session expired due to inactivity"

        # Rotate tokens
        session.status = "REVOKED"
        session.revoked_at = datetime.utcnow()
        self.session_repo.save(session)

        new_jti = str(uuid.uuid4())
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None, "User inactive or disabled"

        new_access_token = create_access_token(subject=user.id, role=user.role, jti=new_jti)
        new_refresh_token = create_refresh_token(subject=user.id, jti=new_jti)

        new_session = UserSession(
            user_id=user.id,
            refresh_token_jti=new_jti,
            status="ACTIVE",
            device_name=parse_device(user_agent) if user_agent else session.device_name,
            browser=parse_browser(user_agent) if user_agent else session.browser,
            operating_system=parse_os(user_agent) if user_agent else session.operating_system,
            ip_address=ip_address or session.ip_address,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            last_activity=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        self.session_repo.create(new_session)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }, None

    def logout_user(self, refresh_token: str) -> Tuple[bool, Optional[str]]:
        payload = decode_token(refresh_token, is_refresh=True)
        if not payload:
            return False, "Invalid refresh token"

        jti = payload.get("jti")
        if not jti:
            return False, "Invalid refresh token payload"

        session = self.session_repo.get_by_jti(jti)
        if session:
            session.status = "REVOKED"
            session.revoked_at = datetime.utcnow()
            self.session_repo.save(session)
            if self.event_publisher:
                self.event_publisher.publish("SESSION_REVOKED", {"user_id": session.user_id, "session_id": session.id})
                self.event_publisher.publish("LOGOUT", {"user_id": session.user_id})
        return True, None

    def verify_email(self, token: str) -> Tuple[bool, Optional[str]]:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user = self.user_repo.get_by_verification_token(token_hash)
        if not user or (user.verification_token_expiry and user.verification_token_expiry < datetime.utcnow()):
            return False, "Invalid or expired verification token"

        user.is_verified = True
        user.verification_token_hash = None
        user.verification_token_expiry = None
        self.user_repo.save(user)

        if self.event_publisher:
            self.event_publisher.publish("EMAIL_VERIFIED", {"user_id": user.id, "email": user.email})

        return True, None

    def resend_verification(self, email: str) -> Tuple[bool, Optional[str]]:
        user = self.user_repo.get_by_email_with_lock(email)
        if not user:
            return False, "User not found"

        if user.is_verified:
            return False, "Email already verified"

        verification_token = secrets.token_urlsafe(32)
        user.verification_token_hash = hashlib.sha256(verification_token.encode()).hexdigest()
        user.verification_token_expiry = datetime.utcnow() + timedelta(hours=24)
        self.user_repo.save(user)

        if self.event_publisher:
            self.event_publisher.publish("USER_REGISTERED", {
                "user_id": user.id,
                "email": user.email,
                "verification_token": verification_token
            })

        return True, None

    def forgot_password(self, email: str) -> Tuple[bool, Optional[str]]:
        # Enforce blind success response to mitigate account harvesting
        user = self.user_repo.get_by_email(email)
        if not user:
            return True, None

        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
        user.password_reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
        self.user_repo.save(user)

        if self.event_publisher:
            self.event_publisher.publish("PASSWORD_RESET_REQUESTED", {
                "user_id": user.id,
                "email": user.email,
                "reset_token": reset_token
            })

        return True, None

    def reset_password(self, token: str, new_password_plain: str) -> Tuple[bool, Optional[str]]:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user = self.user_repo.get_by_password_reset_token(token_hash)
        if not user or (user.password_reset_token_expiry and user.password_reset_token_expiry < datetime.utcnow()):
            return False, "Invalid or expired password reset token"

        # Validate password strength policies
        is_valid, err_msg = validate_password_strength(new_password_plain)
        if not is_valid:
            return False, err_msg

        user.hashed_password = get_password_hash(new_password_plain)
        user.password_reset_token_hash = None
        user.password_reset_token_expiry = None
        user.login_attempts = 0
        user.locked_until = None
        self.user_repo.save(user)

        if self.event_publisher:
            self.event_publisher.publish("PASSWORD_RESET_COMPLETED", {"user_id": user.id, "email": user.email})

        return True, None
