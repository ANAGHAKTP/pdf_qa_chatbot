import uuid
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy.orm import Session, sessionmaker
from app.repositories.audit import AuditLogRepository
from app.db.models import AuditLog


class AuditLogService:
    def __init__(self, db: Optional[Session] = None, db_session_factory: Optional[sessionmaker] = None):
        self.db = db
        if db:
            self.audit_repo = AuditLogRepository(db)
        else:
            self.audit_repo = None
        self.db_session_factory = db_session_factory

    def log_event(
        self,
        user_id: Optional[int],
        event_type: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> AuditLog:
        audit_log = AuditLog(
            event_id=str(uuid.uuid4()),
            request_id=request_id,
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=metadata,
            timestamp=datetime.utcnow()
        )
        
        if self.db_session_factory:
            db = self.db_session_factory()
            try:
                repo = AuditLogRepository(db)
                result = repo.create(audit_log)
                return result
            finally:
                db.close()
        else:
            return self.audit_repo.create(audit_log)

    def list_logs_for_user(self, user_id: int, skip: int = 0, limit: int = 50) -> List[AuditLog]:
        if self.db_session_factory:
            db = self.db_session_factory()
            try:
                repo = AuditLogRepository(db)
                return repo.get_by_user(user_id, skip=skip, limit=limit)
            finally:
                db.close()
        else:
            return self.audit_repo.get_by_user(user_id, skip=skip, limit=limit)

    # Decoupled Event Listeners
    def _log_from_event(self, event_type: str, event) -> None:
        payload = event.payload
        user_id = payload.get("user_id")
        
        # Read request-local correlation variables
        from app.core.logging import request_context
        ctx = request_context.get()
        
        self.log_event(
            user_id=user_id,
            event_type=event_type,
            request_id=ctx.get("request_id"),
            ip_address=payload.get("ip_address") or ctx.get("ip_address"),
            user_agent=payload.get("user_agent") or ctx.get("user_agent"),
            metadata=payload
        )

    def handle_login_success(self, event) -> None:
        self._log_from_event("LOGIN_SUCCESS", event)

    def handle_login_failed(self, event) -> None:
        self._log_from_event("LOGIN_FAILED", event)

    def handle_logout(self, event) -> None:
        self._log_from_event("LOGOUT", event)

    def handle_password_reset_requested(self, event) -> None:
        self._log_from_event("PASSWORD_RESET_REQUESTED", event)

    def handle_password_reset_completed(self, event) -> None:
        self._log_from_event("PASSWORD_RESET_COMPLETED", event)

    def handle_email_verified(self, event) -> None:
        self._log_from_event("EMAIL_VERIFIED", event)

    def handle_account_locked(self, event) -> None:
        self._log_from_event("ACCOUNT_LOCKED", event)

    def handle_session_revoked(self, event) -> None:
        self._log_from_event("SESSION_REVOKED", event)

    def handle_session_revoked_others(self, event) -> None:
        self._log_from_event("SESSION_REVOKED_OTHERS", event)
