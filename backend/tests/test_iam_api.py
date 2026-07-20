import pytest
import uuid
import json
from fastapi.testclient import TestClient
from app.main import app
from app.core import metrics


@pytest.fixture(autouse=True)
def configure_strict_passwords():
    from app.core.config import settings
    # Save original settings
    orig_len = settings.PASSWORD_MIN_LENGTH
    orig_upper = settings.PASSWORD_REQUIRE_UPPERCASE
    orig_lower = settings.PASSWORD_REQUIRE_LOWERCASE
    orig_num = settings.PASSWORD_REQUIRE_NUMBER
    orig_special = settings.PASSWORD_REQUIRE_SPECIAL

    # Set strict values for IAM API tests
    settings.PASSWORD_MIN_LENGTH = 12
    settings.PASSWORD_REQUIRE_UPPERCASE = True
    settings.PASSWORD_REQUIRE_LOWERCASE = True
    settings.PASSWORD_REQUIRE_NUMBER = True
    settings.PASSWORD_REQUIRE_SPECIAL = True

    yield

    # Restore original settings
    settings.PASSWORD_MIN_LENGTH = orig_len
    settings.PASSWORD_REQUIRE_UPPERCASE = orig_upper
    settings.PASSWORD_REQUIRE_LOWERCASE = orig_lower
    settings.PASSWORD_REQUIRE_NUMBER = orig_num
    settings.PASSWORD_REQUIRE_SPECIAL = orig_special


def test_openapi_schema_contains_new_iam_endpoints(client):
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    
    paths = schema["paths"]
    
    # Assert new REST endpoints are exposed with detailed descriptions and summaries
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/auth/verify-email" in paths
    assert "/api/v1/auth/resend-verification" in paths
    assert "/api/v1/auth/forgot-password" in paths
    assert "/api/v1/auth/reset-password" in paths


def test_api_registration_validation_fails_on_weak_password(client):
    # Weak password should trigger a validation 400 Bad Request error under strict settings
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak_api@test.com",
            "password": "weak",  # Password does not satisfy strict policy
            "full_name": "API User"
        }
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_api_verify_email_flow(client, db_session):
    # Register a new user with complex password
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "verify_api@test.com",
            "password": "SecurePassword123!",
            "full_name": "Verify API User"
        }
    )
    assert reg_response.status_code == 201
    
    from app.db.models import User
    user = db_session.query(User).filter(User.email == "verify_api@test.com").first()
    assert user.is_verified is False
    assert user.verification_token_hash is not None

    # Verify that calling verify-email with invalid token fails
    fail_response = client.post(
        "/api/v1/auth/verify-email",
        json={"token": "invalid_token_123"}
    )
    assert fail_response.status_code == 400
    assert "Invalid or expired" in fail_response.json()["detail"]


def test_api_resend_verification_validation(client):
    # Call resend verification for non-existent user
    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "non_existent_api@test.com"}
    )
    assert response.status_code == 400
    assert "User not found" in response.json()["detail"]


def test_api_forgot_password_blind_success(client):
    # Call forgot password: must return success 200 even for non-existent users (blind success)
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "non_existent_forgot_api@test.com"}
    )
    assert response.status_code == 200
    assert "If the email is registered, a password reset link has been sent" in response.json()["message"]


def test_api_logout_invalid_token_fails(client):
    # Call logout with garbage token
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "garbage_refresh_token_123"}
    )
    assert response.status_code == 400
    assert "Invalid refresh token" in response.json()["detail"]
