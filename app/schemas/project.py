from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Название проекта")
    description: Optional[str] = Field(None, max_length=1000, description="Описание проекта")
    client: Optional[str] = Field(None, max_length=200, description="Клиент")
    station: Optional[str] = Field(None, max_length=200, description="Станция")
    unit: Optional[int] = Field(None, description="Номер блока")
    type: Optional[str] = Field(None, max_length=200, description="Тип системы")
    
    contact_name: Optional[str] = Field(None, max_length=200, description="ФИО ответственного")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Телефон")
    contact_email: Optional[str] = Field(None, max_length=200, description="Email")
    contact_position: Optional[str] = Field(None, max_length=200, description="Должность")

    @validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Запрещает пустое или состоящее из пробелов название проекта."""
        if not v or not v.strip():
            raise ValueError("Название проекта не может быть пустым")
        return v.strip()


class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    """Схема для обновления проекта (все поля опциональны)."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    client: Optional[str] = Field(None, max_length=200)
    station: Optional[str] = Field(None, max_length=200)
    unit: Optional[int] = Field(None)
    type: Optional[str] = Field(None, max_length=200)
    
     # Контактная информация
    contact_name: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    contact_position: Optional[str] = Field(None, max_length=200)

    @validator('name')
    def name_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Название проекта не может быть пустым')
        return v.strip() if v else v


class ProjectResponse(ProjectBase):
    """Схема ответа API с ID и датами создания/обновления."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        """Настройки Pydantic-модели."""

        from_attributes = True  # Поддержка чтения из ORM-объектов (Pydantic v2)
