def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ops@shipguard.local", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ops@shipguard.local", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@domain.com", "password": "admin123"}
    )
    assert response.status_code == 401


def test_protected_route_without_token(client):
    response = client.get("/api/v1/shipments")
    assert response.status_code in (401, 403)
