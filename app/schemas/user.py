"""Pydantic-схемы для сущности «Пользователь» и аутентификации."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserRole(str, Enum):
    """Роли пользователей системы."""

    ADMIN = "admin"
    ENGINEER = "engineer"
    MANAGER = "manager"


class UserBase(BaseModel):
    """Базовая схема пользователя с общими полями."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.MANAGER


class UserCreate(UserBase):
    """Схема для создания пользователя (требует пароль)."""

    password: str = Field(..., min_length=6, max_length=100)

    @validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Проверяет минимальную длину пароля с понятным сообщением об ошибке.

        Дублирует ограничение Field(min_length=6), но даёт более
        читаемый текст ошибки для клиента API.
        """
        if len(v) < 6:
            raise ValueError("Пароль должен быть не менее 6 символов")
        return v


class UserLogin(BaseModel):
    """Схема для входа пользователя в систему."""

    username: str
    password: str


class UserUpdate(BaseModel):
    """Схема для обновления пользователя (все поля опциональны)."""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """Схема ответа API с данными пользователя."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Настройки Pydantic-модели."""

        from_attributes = True


class Token(BaseModel):
    """Схема JWT-токена доступа, возвращаемого после аутентификации."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Данные, извлекаемые из payload JWT-токена."""

    username: Optional[str] = None
    role: Optional[str] = None
