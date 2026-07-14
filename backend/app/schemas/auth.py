from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLoginResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_admin: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: Optional[UserLoginResponse] = None
