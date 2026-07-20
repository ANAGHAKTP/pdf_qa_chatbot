def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@docmind.com",
            "password": "securepassword",
            "full_name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@docmind.com"
    assert data["full_name"] == "New User"
    assert "id" in data
    assert data["is_active"] is True


def test_register_user_already_exists(client, test_user):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "anotherpassword",
            "full_name": "Duplicate User"
        }
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_login_oauth2(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user.email


def test_login_json(client, test_user):
    response = client.post(
        "/api/v1/auth/login-json",
        json={
            "email": test_user.email,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == test_user.email


def test_login_incorrect_password(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_get_me(client, test_user):
    # First login to get access token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "password123"
        }
    )
    access_token = login_response.json()["access_token"]
    
    # Call me endpoint
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_iam_database_behavior(db_session):
    import uuid
    from datetime import datetime, timedelta
    from app.db.models import User, UserSession, AuditLog
    import pytest
    from sqlalchemy.exc import IntegrityError

    # 1. Verify multiple null values are allowed for token hashes
    user1 = User(
        email="test_iam_u1@docmind.com",
        hashed_password="...",
        verification_token_hash=None,
        password_reset_token_hash=None
    )
    user2 = User(
        email="test_iam_u2@docmind.com",
        hashed_password="...",
        verification_token_hash=None,
        password_reset_token_hash=None
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()

    # 2. Token hashes must remain unique when populated
    hash_val = "sha256_hash_123"
    user1.verification_token_hash = hash_val
    db_session.commit()

    # Wrap savepoint nested transaction
    try:
        with db_session.begin_nested():
            user2.verification_token_hash = hash_val
            db_session.flush()
        raise AssertionError("IntegrityError was not raised for duplicate hashes")
    except IntegrityError:
        pass

    # 3. Verify clearing token allows reuse
    user1.verification_token_hash = None
    db_session.commit()

    user2.verification_token_hash = hash_val
    db_session.commit()

    # 4. Verify cascade delete and set null behavior
    user3 = User(
        email="test_iam_u3@docmind.com",
        hashed_password="..."
    )
    db_session.add(user3)
    db_session.commit()

    session = UserSession(
        user_id=user3.id,
        refresh_token_jti="jti_xyz_123",
        status="ACTIVE",
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    audit_log = AuditLog(
        event_id=str(uuid.uuid4()),
        user_id=user3.id,
        event_type="LOGIN_SUCCESS"
    )
    db_session.add(session)
    db_session.add(audit_log)
    db_session.commit()

    session_id = session.id
    audit_log_id = audit_log.id

    db_session.delete(user3)
    db_session.commit()

    deleted_session = db_session.query(UserSession).filter(UserSession.id == session_id).first()
    assert deleted_session is None

    preserved_log = db_session.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
    assert preserved_log is not None
    assert preserved_log.user_id is None

