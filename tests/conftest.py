import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.all_models import User, Project, Fault, KnowledgeBase
from app.schemas.user import UserRole


# Тестовая база данных SQLite в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_faults.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Переопределяем зависимость get_db для тестов
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Создание сессии БД для тестов"""
    # Создаём таблицы
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Очищаем после тестов
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Тестовый клиент FastAPI"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_user(db_session):
    """Создание тестового пользователя"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("test123"),
        full_name="Test User",
        role=UserRole.MANAGER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin(db_session):
    """Создание тестового администратора"""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("admin123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_project(db_session, test_user):
    """Создание тестового проекта"""
    project = Project(
        name="Тестовый проект",
        description="Описание тестового проекта",
        client="Тестовый клиент",
        station="Тестовая станция",
        unit=1,
        type="САРЗ"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
def test_fault(db_session, test_project):
    """Создание тестовой неисправности"""
    fault = Fault(
        title="Тестовая неисправность",
        description="Описание тестовой неисправности",
        severity="critical",
        status="open",
        project_id=test_project.id
    )
    db_session.add(fault)
    db_session.commit()
    db_session.refresh(fault)
    return fault


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """Получение JWT токена для тестового пользователя"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "test123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Заголовки с токеном авторизации"""
    return {"Authorization": f"Bearer {auth_token}"}