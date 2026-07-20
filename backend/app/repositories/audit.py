from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, audit_log: AuditLog) -> AuditLog:
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 50) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    def count_by_user(self, user_id: int) -> int:
        return self.db.query(AuditLog).filter(AuditLog.user_id == user_id).count()

    def delete_old_logs(self, retention_date) -> int:
        deleted = self.db.query(AuditLog).filter(
            AuditLog.timestamp < retention_date
        ).delete(synchronize_session=False)
        self.db.commit()
        return deleted
