import pytest
from datetime import datetime, timedelta
from fastapi import status
from app.db.models import User, UserSession
from app.core.security import create_access_token, create_refresh_token
from app.core.events import event_publisher


def test_unauthorized_session_endpoints(client):
    # Missing bearer header: must reject with 401 Unauthorized
    response_list = client.get("/api/v1/sessions")
    assert response_list.status_code == status.HTTP_401_UNAUTHORIZED
    
    response_revoke = client.delete("/api/v1/sessions/1")
    assert response_revoke.status_code == status.HTTP_401_UNAUTHORIZED
    
    response_revoke_others = client.delete("/api/v1/sessions/others")
    assert response_revoke_others.status_code == status.HTTP_401_UNAUTHORIZED


def test_session_listing_and_current_indicator(client, db_session, test_user):
    # Generate token matching user. Set active JTI.
    jti_current = "jti-active-111"
    token = create_access_token(subject=test_user.id, role=test_user.role, jti=jti_current)
    headers = {"Authorization": f"Bearer {token}"}
    
    now = datetime.utcnow()
    # Add active sessions to DB
    s1 = UserSession(
        refresh_token_jti=jti_current,
        user_id=test_user.id,
        status="ACTIVE",
        browser="Chrome",
        operating_system="Windows",
        expires_at=now + timedelta(hours=1)
    )
    s2 = UserSession(
        refresh_token_jti="jti-other-222",
        user_id=test_user.id,
        status="ACTIVE",
        browser="Safari",
        operating_system="iOS",
        expires_at=now + timedelta(hours=1)
    )
    
    db_session.add_all([s1, s2])
    db_session.commit()
    
    response = client.get("/api/v1/sessions", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Assert active sessions returned
    assert len(data) == 2
    
    # Assert the correct session indicates "is_current"
    current_session = next(s for s in data if s["id"] == s1.id)
    other_session = next(s for s in data if s["id"] == s2.id)
    
    assert current_session["is_current"] is True
    assert other_session["is_current"] is False


def test_session_ownership_protection(client, db_session, test_user, admin_user):
    # User 1 token
    token1 = create_access_token(subject=test_user.id, role=test_user.role, jti="user-jti")
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    # Create active session belonging to User 2 (admin_user)
    session_admin = UserSession(
        refresh_token_jti="admin-jti",
        user_id=admin_user.id,
        status="ACTIVE",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(session_admin)
    db_session.commit()
    
    # User 1 attempts to delete User 2's session
    response = client.delete(f"/api/v1/sessions/{session_admin.id}", headers=headers1)
    
    # Must return 404 (not leak user session existence)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_revoke_specific_session_flow(client, db_session, test_user):
    token = create_access_token(subject=test_user.id, role=test_user.role, jti="current-jti")
    headers = {"Authorization": f"Bearer {token}"}
    
    session = UserSession(
        refresh_token_jti="target-jti",
        user_id=test_user.id,
        status="ACTIVE",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(session)
    db_session.commit()

    # Clear previous publisher logs
    events = []
    def spy_callback(event):
        events.append(event)
    event_publisher.subscribe("SESSION_REVOKED", spy_callback)

    response = client.delete(f"/api/v1/sessions/{session.id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Session successfully revoked"
    
    # Verify session is marked REVOKED in DB
    db_session.refresh(session)
    assert session.status == "REVOKED"
    assert session.revoked_at is not None
    
    # Wait dynamically for background thread event delivery
    import time
    start_time = time.time()
    while len(events) == 0 and (time.time() - start_time) < 2.0:
        time.sleep(0.05)
        
    # Verify SESSION_REVOKED event was dispatched
    assert len(events) >= 1
    assert events[-1].event_type == "SESSION_REVOKED"
    assert events[-1].payload["session_id"] == session.id


def test_revoke_other_sessions_flow(client, db_session, test_user):
    token = create_access_token(subject=test_user.id, role=test_user.role, jti="current-jti")
    headers = {"Authorization": f"Bearer {token}"}
    
    s_current = UserSession(
        refresh_token_jti="current-jti",
        user_id=test_user.id,
        status="ACTIVE",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    s_other1 = UserSession(
        refresh_token_jti="other-jti-1",
        user_id=test_user.id,
        status="ACTIVE",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    s_other2 = UserSession(
        refresh_token_jti="other-jti-2",
        user_id=test_user.id,
        status="ACTIVE",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    
    db_session.add_all([s_current, s_other1, s_other2])
    db_session.commit()
    
    events = []
    def spy_callback(event):
        events.append(event)
    event_publisher.subscribe("SESSION_REVOKED_OTHERS", spy_callback)
    
    response = client.delete("/api/v1/sessions/others", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert "revoked 2 other sessions" in response.json()["message"]
    
    db_session.refresh(s_current)
    db_session.refresh(s_other1)
    db_session.refresh(s_other2)
    
    # Current session remains active, others are revoked
    assert s_current.status == "ACTIVE"
    assert s_other1.status == "REVOKED"
    assert s_other2.status == "REVOKED"
    
    # Wait dynamically for background thread event delivery
    import time
    start_time = time.time()
    while len(events) == 0 and (time.time() - start_time) < 2.0:
        time.sleep(0.05)
        
    # Verify SESSION_REVOKED_OTHERS event was dispatched
    assert len(events) >= 1
    assert events[-1].event_type == "SESSION_REVOKED_OTHERS"
    assert events[-1].payload["count"] == 2
