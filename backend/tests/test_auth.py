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
