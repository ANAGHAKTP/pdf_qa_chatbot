from datetime import timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.repositories.user import UserRepository
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.db.models import User


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register_user(self, email: str, password_plain: str, full_name: Optional[str] = None) -> Tuple[Optional[User], Optional[str]]:
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            return None, "Email already registered"
        
        # Determine if this is the first user; if so, make them admin
        user_count = self.user_repo.count_users()
        is_admin = (user_count == 0)
        
        user = self.user_repo.create(
            email=email,
            password_plain=password_plain,
            full_name=full_name,
            is_admin=is_admin
        )
        return user, None

    def authenticate_user(self, email: str, password_plain: str) -> Tuple[Optional[User], Optional[str]]:
        user = self.user_repo.get_by_email(email)
        if not user:
            return None, "Invalid email or password"
        
        if not user.is_active:
            return None, "User account is disabled"
            
        if not verify_password(password_plain, user.hashed_password):
            return None, "Invalid email or password"
            
        return user, None

    def login_user(self, email: str, password_plain: str) -> Tuple[Optional[dict], Optional[str]]:
        user, err = self.authenticate_user(email, password_plain)
        if err:
            return None, err
            
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin
            }
        }, None

    def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[dict], Optional[str]]:
        payload = decode_token(refresh_token, is_refresh=True)
        if not payload or payload.get("type") != "refresh":
            return None, "Invalid refresh token"
            
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None, "Invalid refresh token subject"
            
        try:
            user_id = int(user_id_str)
        except ValueError:
            return None, "Invalid user ID in token"
            
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None, "User not found or inactive"
            
        new_access_token = create_access_token(subject=user.id)
        # Optionally create a new refresh token (token rotation)
        new_refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }, None
