import pytest
from app.core.security import verify_password
from app.models.all_models import User


def test_register_user(client, db_session):
    """Тест регистрации нового пользователя"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User",
            "role": "manager"
        }
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
            "full_name": "Another User"
        }
    )
    
    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]


def test_login_success(client, test_user):
    """Тест успешного входа"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "test123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"


def test_login_wrong_password(client, test_user):
    """Тест входа с неверным паролем"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 401
    assert "Неверное имя пользователя или пароль" in response.json()["detail"]


def test_get_current_user(client, auth_headers):
    """Тест получения текущего пользователя"""
    response = client.get(
        "/api/auth/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_get_current_user_unauthorized(client):
    """Тест получения пользователя без токена"""
    response = client.get("/api/auth/me")
    
    assert response.status_code == 401