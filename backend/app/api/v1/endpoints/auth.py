from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import UserRegister, TokenResponse, TokenRefreshRequest, UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    auth_service = AuthService(db)
    user, err = auth_service.register_user(
        email=user_in.email,
        password_plain=user_in.password,
        full_name=user_in.full_name
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err
        )
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, retrieve access and refresh tokens.
    """
    auth_service = AuthService(db)
    result, err = auth_service.login_user(
        email=form_data.username,
        password_plain=form_data.password
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


@router.post("/login-json", response_model=TokenResponse)
def login_json(
    credentials: UserRegister,  # Reuse email/password, full_name is ignored
    db: Session = Depends(get_db)
):
    """
    Standard JSON login endpoint for clients.
    """
    auth_service = AuthService(db)
    result, err = auth_service.login_user(
        email=credentials.email,
        password_plain=credentials.password
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err,
        )
    return result


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_in: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Get a new access token using a refresh token.
    """
    auth_service = AuthService(db)
    result, err = auth_service.refresh_access_token(refresh_in.refresh_token)
    if err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err
        )
    return result


@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get profile details of the current logged-in user.
    """
    return current_user
