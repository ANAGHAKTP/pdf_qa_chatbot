from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api import deps
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import (
    UserRegister, 
    TokenResponse, 
    TokenRefreshRequest, 
    UserResponse,
    EmailVerifyRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    LogoutRequest
)
from app.services.auth import AuthService
from app.core.events import event_publisher

router = APIRouter()


@router.post(
    "/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user profile",
    description="Registers a user account, hashes credentials, initializes role configuration, and dispatches activation verification emails.",
    responses={
        400: {"description": "Invalid payload validation or email already registered."}
    }
)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db, event_publisher=event_publisher)
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


@router.post(
    "/login", 
    response_model=TokenResponse,
    summary="OAuth2 Form credentials login",
    description="Authenticates username/password form inputs, records device telemetry metadata, tracks failure attempts, and issues token pairs.",
    responses={
        401: {"description": "Invalid credentials or account has been locked."}
    }
)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    auth_service = AuthService(db, event_publisher=event_publisher)
    result, err = auth_service.login_user(
        email=form_data.username,
        password_plain=form_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


@router.post(
    "/login-json", 
    response_model=TokenResponse,
    summary="JSON structured credentials login",
    description="Authenticates structured JSON inputs, records device telemetry, checks lockout states, and issues rotated token pairs.",
    responses={
        401: {"description": "Invalid credentials or account has been locked."}
    }
)
def login_json(
    request: Request,
    credentials: UserRegister,
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    auth_service = AuthService(db, event_publisher=event_publisher)
    result, err = auth_service.login_user(
        email=credentials.email,
        password_plain=credentials.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err,
        )
    return result


@router.post(
    "/refresh", 
    response_model=TokenResponse,
    summary="Rotate active refresh token",
    description="Validates the client refresh token, enforces inactivity limits, rotates the JTI ID, and invalidates older sessions.",
    responses={
        401: {"description": "Refresh token is expired, revoked, or replay attack detected."}
    }
)
def refresh_token(
    request: Request,
    refresh_in: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    auth_service = AuthService(db, event_publisher=event_publisher)
    result, err = auth_service.refresh_access_token(
        refresh_token=refresh_in.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err
        )
    return result


@router.post(
    "/logout",
    summary="Invalidate active user session",
    description="Decodes client refresh token payload, invalidates the JTI record, marks user session as REVOKED, and dispatches logout telemetry.",
    responses={
        400: {"description": "Invalid token signature or session ID not found."}
    }
)
def logout(
    logout_in: LogoutRequest,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db, event_publisher=event_publisher)
    success, err = auth_service.logout_user(refresh_token=logout_in.refresh_token)
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err
        )
    return {"message": "Logged out successfully"}


@router.post(
    "/verify-email",
    summary="Validate email verification token",
    description="Hashes token string, marks profile as verified in database, and nullifies verification parameters.",
    responses={
        400: {"description": "Invalid, missing, or expired activation token."}
    }
)
def verify_email(
    verify_in: EmailVerifyRequest,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db, event_publisher=event_publisher)
    success, err = auth_service.verify_email(token=verify_in.token)
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err
        )
    return {"message": "Email verified successfully"}


@router.post(
    "/resend-verification",
    summary="Resend account verification links",
    description="Locks profile row, checks verification status, generates new token hashes, and publishes activation mail requests.",
    responses={
        400: {"description": "User profile not found or email has already been verified."}
    }
)
def resend_verification(
    resend_in: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db, event_publisher=event_publisher)
    success, err = auth_service.resend_verification(email=resend_in.email)
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err
        )
    return {"message": "Verification email sent successfully"}


@router.post(
    "/forgot-password",
    summary="Request password recovery link",
    description="Generates password reset token, commits expiry dates, and dispatches reset notification. Emits blind success responses.",
    responses={
        200: {"description": "Recovery process initiated successfully (blind success)."}
    }
)
def forgot_password(
    forgot_in: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db, event_publisher=event_publisher)
    # Always returns True to mitigate user enumerations
    success, err = auth_service.forgot_password(email=forgot_in.email)
    return {"message": "If the email is registered, a password reset link has been sent"}


@router.post(
    "/reset-password",
    summary="Complete password recovery flow",
    description="Validates recovery token, enforces complexity settings, hashes new credentials, and clears locked states.",
    responses={
        400: {"description": "Token has expired or new password does not meet complexity requirements."}
    }
)
def reset_password(
    reset_in: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db, event_publisher=event_publisher)
    success, err = auth_service.reset_password(
        token=reset_in.token,
        new_password_plain=reset_in.new_password
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err
        )
    return {"message": "Password reset successfully"}


@router.get(
    "/me", 
    response_model=UserResponse,
    summary="Get current profile details",
    description="Validates authorization bearer access token and returns details of the currently logged-in user."
)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    return current_user
