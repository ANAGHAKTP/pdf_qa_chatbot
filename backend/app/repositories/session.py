from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import UserSession


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_jti(self, jti: str) -> Optional[UserSession]:
        return self.db.query(UserSession).filter(UserSession.refresh_token_jti == jti).first()

    def get_active_by_user(self, user_id: int) -> List[UserSession]:
        return self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.status == "ACTIVE"
        ).all()

    def create(self, session: UserSession) -> UserSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def save(self, session: UserSession) -> UserSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def revoke_all_for_user(self, user_id: int, exclude_jti: Optional[str] = None) -> int:
        query = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.status == "ACTIVE"
        )
        if exclude_jti:
            query = query.filter(UserSession.refresh_token_jti != exclude_jti)
        
        sessions = query.all()
        for s in sessions:
            s.status = "REVOKED"
            s.revoked_at = s.last_activity
        
        self.db.commit()
        return len(sessions)

    def clear_expired_sessions(self, now) -> int:
        marked = self.db.query(UserSession).filter(
            UserSession.status == "ACTIVE",
            UserSession.expires_at < now
        ).update(
            {UserSession.status: "EXPIRED"},
            synchronize_session=False
        )
        
        from datetime import timedelta
        retention_limit = now - timedelta(days=30)
        deleted = self.db.query(UserSession).filter(
            UserSession.status.in_(["EXPIRED", "REVOKED"]),
            UserSession.expires_at < retention_limit
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return marked + deleted
