import pytest
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from app.db.models import User, Role
from app.api import deps
from app.core.security import create_access_token


# Declare dynamic routes for RBAC testing on the FastAPI app instance
# Avoid starting endpoint function names with "test_" to prevent pytest parsing them as test cases!
from app.main import app

@app.get("/api/v1/test-rbac-user-helper")
def rbac_user_route(current_user: User = Depends(deps.require_role(Role.USER))):
    return {"message": "Success", "email": current_user.email}

@app.get("/api/v1/test-rbac-any-helper")
def rbac_any_route(current_user: User = Depends(deps.require_any_role([Role.USER, Role.ADMIN]))):
    return {"message": "Success", "email": current_user.email}


def test_require_authenticated_user_unauthorized(client):
    # No auth header -> 401 Unauthorized
    response = client.get("/api/v1/test-rbac-user-helper")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_require_role_user_success(client, test_user):
    # USER role calling USER endpoint -> 200 OK
    token = create_access_token(subject=test_user.id, role=test_user.role)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/test-rbac-user-helper", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == test_user.email


def test_require_role_admin_forbidden_for_user(client, test_user):
    # USER role calling ADMIN endpoint (/api/v1/admin/stats) -> 403 Forbidden
    token = create_access_token(subject=test_user.id, role=test_user.role)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/admin/stats", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "requires role" in response.json()["detail"] or "enough privileges" in response.json()["detail"]


def test_require_role_admin_success(client, admin_user):
    # ADMIN role calling ADMIN endpoint (/api/v1/admin/stats) -> 200 OK
    token = create_access_token(subject=admin_user.id, role=admin_user.role)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/admin/stats", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_require_any_role_success(client, test_user, admin_user):
    # Both USER and ADMIN roles can access the test-rbac-any endpoint
    token_user = create_access_token(subject=test_user.id, role=test_user.role)
    response_user = client.get("/api/v1/test-rbac-any-helper", headers={"Authorization": f"Bearer {token_user}"})
    assert response_user.status_code == status.HTTP_200_OK
    
    token_admin = create_access_token(subject=admin_user.id, role=admin_user.role)
    response_admin = client.get("/api/v1/test-rbac-any-helper", headers={"Authorization": f"Bearer {token_admin}"})
    assert response_admin.status_code == status.HTTP_200_OK


def test_require_any_role_forbidden(client, db_session, test_user):
    # Temporarily change test_user role to an invalid custom string to test failure
    original_role = test_user.role
    test_user.role = "GUEST"
    db_session.add(test_user)
    db_session.commit()
    
    try:
        token = create_access_token(subject=test_user.id, role="GUEST")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/test-rbac-any-helper", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "requires one of the roles" in response.json()["detail"]
    finally:
        # Restore original role
        test_user.role = original_role
        db_session.add(test_user)
        db_session.commit()
