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


def test_google_auth_new_user(client, monkeypatch):
    from google.oauth2 import id_token

    def mock_verify_oauth2_token(token_str, request, audience=None):
        return {
            "iss": "https://accounts.google.com",
            "email": "new.google.user@example.com",
            "email_verified": True,
            "name": "Google Test User",
        }

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify_oauth2_token)

    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "valid-mock-google-id-token-xyz"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_google_auth_existing_user(client, monkeypatch):
    from google.oauth2 import id_token

    def mock_verify_oauth2_token(token_str, request, audience=None):
        return {
            "iss": "accounts.google.com",
            "email": "ops@shipguard.local",
            "email_verified": True,
            "name": "Ops User",
        }

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify_oauth2_token)

    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "valid-mock-google-id-token-ops"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_google_auth_unverified_email_rejected(client, monkeypatch):
    from google.oauth2 import id_token

    def mock_verify_oauth2_token(token_str, request, audience=None):
        return {
            "iss": "https://accounts.google.com",
            "email": "unverified@example.com",
            "email_verified": False,
            "name": "Unverified User",
        }

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify_oauth2_token)

    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "mock-unverified-token"}
    )
    assert response.status_code == 400
    assert "not been verified" in response.json()["detail"]


def test_google_auth_invalid_token_rejected(client, monkeypatch):
    from google.oauth2 import id_token

    def mock_verify_oauth2_token(token_str, request, audience=None):
        raise ValueError("Token is expired or invalid signature")

    monkeypatch.setattr(id_token, "verify_oauth2_token", mock_verify_oauth2_token)

    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "invalid-garbage-token"}
    )
    assert response.status_code == 401
    assert "Google authentication failed" in response.json()["detail"]
