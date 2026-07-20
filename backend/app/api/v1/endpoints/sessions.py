from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import jwt

from app.api import deps
from app.db.session import get_db
from app.db.models import User, UserSession
from app.core.config import settings
from app.core.events import event_publisher
from app.services.session import SessionService
from app.schemas.auth import SessionResponse  # Wait! We need to define SessionResponse in schemas

router = APIRouter()


def get_current_token_jti(token: str = Depends(deps.oauth2_scheme)) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("jti")
    except Exception:
        return None


@router.get(
    "", 
    response_model=List[SessionResponse],
    summary="List active user sessions",
    description="Returns a list of all active sessions for the current authenticated user, indicating which session correlates to the current request."
)
def list_sessions(
    current_user: User = Depends(deps.get_current_active_user),
    current_jti: Optional[str] = Depends(get_current_token_jti),
    db: Session = Depends(get_db)
):
    session_service = SessionService(db, event_publisher=event_publisher)
    sessions = session_service.list_active_sessions(current_user.id)
    
    response = []
    for s in sessions:
        is_current = (current_jti is not None and s.refresh_token_jti == current_jti)
        response.append(
            SessionResponse(
                id=s.id,
                device_name=s.device_name,
                browser=s.browser,
                operating_system=s.operating_system,
                ip_address=s.ip_address,
                last_activity=s.last_activity,
                created_at=s.created_at,
                is_current=is_current
            )
        )
    return response


@router.delete(
    "/others",
    summary="Revoke other active sessions",
    description="Revokes all active sessions for the current user except the session associated with the active request token.",
    responses={
        200: {"description": "Other sessions successfully revoked."}
    }
)
def revoke_others(
    current_user: User = Depends(deps.get_current_active_user),
    current_jti: Optional[str] = Depends(get_current_token_jti),
    db: Session = Depends(get_db)
):
    if not current_jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active session ID could not be identified from token context."
        )
        
    session_service = SessionService(db, event_publisher=event_publisher)
    count = session_service.revoke_other_sessions(current_user.id, current_jti)
    return {"message": f"Successfully revoked {count} other sessions"}


@router.delete(
    "/{session_id}",
    summary="Revoke selected session",
    description="Revokes the specified active session. Returns 404 if the session ID does not belong to the user.",
    responses={
        404: {"description": "Session not found."}
    }
)
def revoke_session(
    session_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    session_service = SessionService(db, event_publisher=event_publisher)
    
    # Security: retrieve session and check owner. If not owner, return 404 to prevent info leak!
    s_record = session_service.session_repo.db.query(UserSession).filter(UserSession.id == session_id).first()
    if not s_record or s_record.user_id != current_user.id or s_record.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
        
    session_service.revoke_session(current_user.id, session_id)
    return {"message": "Session successfully revoked"}
