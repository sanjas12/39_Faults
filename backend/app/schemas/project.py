from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class ProjectBase(BaseModel):
    """Базовая схема проекта"""
    name: str = Field(..., min_length=1, max_length=200, description="Название проекта")
    description: Optional[str] = Field(None, max_length=1000, description="Описание проекта")
    client: Optional[str] = Field(None, max_length=200, description="Клиент")
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Название проекта не может быть пустым')
        return v.strip()

class ProjectCreate(ProjectBase):
    """Схема для создания проекта"""
    pass

class ProjectUpdate(BaseModel):
    """Схема для обновления проекта (все поля опциональны)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    client: Optional[str] = Field(None, max_length=200)
    
    @validator('name')
    def name_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Название проекта не может быть пустым')
        return v.strip() if v else v

class ProjectResponse(ProjectBase):
    """Схема для ответа (с ID и датами)"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Для Pydantic v2 (или orm_mode для v1)