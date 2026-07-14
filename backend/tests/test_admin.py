import pytest


def get_auth_headers(client, email, password):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_stats_admin(client, admin_user):
    headers = get_auth_headers(client, admin_user.email, "adminpassword")
    
    response = client.get("/api/v1/admin/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "users_count" in data
    assert "documents_count" in data
    assert "chats_count" in data
    assert "total_storage_mb" in data


def test_get_stats_forbidden_for_user(client, test_user):
    headers = get_auth_headers(client, test_user.email, "password123")
    
    response = client.get("/api/v1/admin/stats", headers=headers)
    assert response.status_code == 403
    assert "privileges" in response.json()["detail"]


def test_get_logs_admin(client, admin_user):
    headers = get_auth_headers(client, admin_user.email, "adminpassword")
    
    response = client.get("/api/v1/admin/logs", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_logs_forbidden_for_user(client, test_user):
    headers = get_auth_headers(client, test_user.email, "password123")
    
    response = client.get("/api/v1/admin/logs", headers=headers)
    assert response.status_code == 403
