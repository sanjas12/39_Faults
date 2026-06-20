"""Pydantic-схемы для сущности «Проект»."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class ProjectBase(BaseModel):
    """Базовая схема проекта с общими полями."""

    name: str = Field(..., min_length=1, max_length=200, description="Название проекта")
    description: Optional[str] = Field(
        None, max_length=1000, description="Описание проекта"
    )
    client: Optional[str] = Field(None, max_length=200, description="Клиент")

    @validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Запрещает пустое или состоящее из пробелов название проекта."""
        if not v or not v.strip():
            raise ValueError("Название проекта не может быть пустым")
        return v.strip()


class ProjectCreate(ProjectBase):
    """Схема для создания проекта."""


class ProjectUpdate(BaseModel):
    """Схема для обновления проекта (все поля опциональны)."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    client: Optional[str] = Field(None, max_length=200)

    @validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Запрещает пустое или состоящее из пробелов название, если оно передано."""
        if v is not None and not v.strip():
            raise ValueError("Название проекта не может быть пустым")
        return v.strip() if v else v


class ProjectResponse(ProjectBase):
    """Схема ответа API с ID и датами создания/обновления."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Настройки Pydantic-модели."""

        from_attributes = True  # Поддержка чтения из ORM-объектов (Pydantic v2)
