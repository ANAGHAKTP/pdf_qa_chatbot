from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import User
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def count_users(self) -> int:
        return self.db.query(User).count()

    def create(self, email: str, password_plain: str, full_name: Optional[str] = None, is_admin: bool = False) -> User:
        hashed_password = get_password_hash(password_plain)
        db_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_admin=is_admin,
            is_active=True
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_profile(self, user_id: int, full_name: Optional[str] = None, password_plain: Optional[str] = None) -> Optional[User]:
        db_user = self.get_by_id(user_id)
        if not db_user:
            return None
        
        if full_name is not None:
            db_user.full_name = full_name
        if password_plain is not None:
            db_user.hashed_password = get_password_hash(password_plain)
            
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_by_email_with_lock(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).with_for_update().first()

    def get_by_verification_token(self, token_hash: str) -> Optional[User]:
        return self.db.query(User).filter(User.verification_token_hash == token_hash).first()

    def get_by_password_reset_token(self, token_hash: str) -> Optional[User]:
        return self.db.query(User).filter(User.password_reset_token_hash == token_hash).first()

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def clear_expired_verification_tokens(self, now) -> int:
        result = self.db.query(User).filter(
            User.verification_token_expiry < now,
            User.verification_token_hash.isnot(None)
        ).update(
            {User.verification_token_hash: None, User.verification_token_expiry: None},
            synchronize_session=False
        )
        self.db.commit()
        return result

    def clear_expired_password_reset_tokens(self, now) -> int:
        result = self.db.query(User).filter(
            User.password_reset_token_expiry < now,
            User.password_reset_token_hash.isnot(None)
        ).update(
            {User.password_reset_token_hash: None, User.password_reset_token_expiry: None},
            synchronize_session=False
        )
        self.db.commit()
        return result
