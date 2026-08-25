def test_register_user(client, db_session):
    """Тест регистрации нового пользователя"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User",
            "role": "manager",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "newuser"
    assert data["user"]["email"] == "newuser@example.com"


def test_register_duplicate_user(client, db_session, test_user):
    """Тест регистрации существующего пользователя"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "test123",
            "full_name": "Another User",
        },
    )

    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]


def test_login_success(client, test_user):
    """Тест успешного входа"""
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "test123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"
    assert response.cookies.get("access_token") == data["access_token"]

    # Проверяем, что TestClient принял cookie в своё хранилище. HTML-маршруты
    # используют отдельную production-сессию БД и не должны проверяться через
    # dependency override тестового API-клиента.
    assert client.cookies.get("access_token") == data["access_token"]


def test_login_wrong_password(client, test_user):
    """Тест входа с неверным паролем"""
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401
    assert "Неверное имя пользователя или пароль" in response.json()["detail"]


def test_logout_clears_browser_session(client, test_user):
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "test123"},
    )
    assert login_response.status_code == 200

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 204
    assert client.cookies.get("access_token") is None


def test_get_current_user(client, auth_headers):
    """Тест получения текущего пользователя"""
    response = client.get("/api/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_get_current_user_unauthorized(client):
    """Тест получения пользователя без токена"""
    response = client.get("/api/auth/me")

    assert response.status_code == 401
