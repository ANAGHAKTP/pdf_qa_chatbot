from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.session import SessionRepository
from app.db.models import UserSession
from app.core.events import EventPublisher


class SessionService:
    def __init__(self, db: Session, event_publisher: Optional[EventPublisher] = None):
        self.session_repo = SessionRepository(db)
        self.event_publisher = event_publisher

    def list_active_sessions(self, user_id: int) -> List[UserSession]:
        return self.session_repo.get_active_by_user(user_id)

    def revoke_session(self, user_id: int, session_id: int) -> bool:
        sessions = self.session_repo.get_active_by_user(user_id)
        session_to_revoke = None
        for s in sessions:
            if s.id == session_id:
                session_to_revoke = s
                break
        
        if not session_to_revoke:
            return False
            
        session_to_revoke.status = "REVOKED"
        from datetime import datetime
        session_to_revoke.revoked_at = datetime.utcnow()
        self.session_repo.save(session_to_revoke)
        
        if self.event_publisher:
            self.event_publisher.publish("SESSION_REVOKED", {
                "user_id": user_id,
                "session_id": session_to_revoke.id,
                "jti": session_to_revoke.refresh_token_jti
            })
        return True

    def revoke_other_sessions(self, user_id: int, current_jti: str) -> int:
        count = self.session_repo.revoke_all_for_user(user_id, exclude_jti=current_jti)
        if count > 0 and self.event_publisher:
            self.event_publisher.publish("SESSION_REVOKED_OTHERS", {
                "user_id": user_id,
                "current_jti": current_jti,
                "count": count
            })
        return count
