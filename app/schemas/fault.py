"""Pydantic-схемы для сущности Fault (неисправность)."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.schemas.comment import CommentResponse
from app.schemas.project import ProjectResponse


class SeverityEnum(str, Enum):
    """Уровень критичности неисправности."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


class StatusEnum(str, Enum):
    """Статус обработки неисправности."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    CLOSED = "closed"


def _normalize_title(title: str) -> str:
    """Удаляет пробелы по краям и проверяет, что название не пустое.

    Args:
        title: Исходное значение поля title.

    Raises:
        ValueError: Если название состоит только из пробелов или пустое.

    Returns:
        Название без пробелов по краям.
    """
    stripped = title.strip()
    if not stripped:
        raise ValueError("Название неисправности не может быть пустым")
    return stripped


class FaultBase(BaseModel):
    """Базовые поля неисправности, общие для создания и отображения."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    severity: SeverityEnum = SeverityEnum.MINOR
    project_id: Optional[int] = Field(None, description="ID проекта (может быть null)")
    linked_knowledge_ids: Optional[str] = Field(None, description="ID статей через запятую")
    planned_actions: Optional[str] = Field(None, description="Планируемые мероприятия (Markdown)")

    @validator("title")
    def title_not_empty(cls, v: str) -> str:  # noqa: N805
        """Проверяет, что название неисправности не пустое."""
        return _normalize_title(v)


class FaultCreate(FaultBase):
    """Схема для создания неисправности."""
    pass


class FaultUpdate(BaseModel):
    """Схема для обновления неисправности (все поля опциональны)."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    severity: Optional[SeverityEnum] = None
    status: Optional[StatusEnum] = None
    project_id: Optional[int] = None
    parent_fault_id: Optional[int] = None
    linked_knowledge_ids: Optional[str] = Field(None, description="ID статей через запятую")
    planned_actions: Optional[str] = Field(None, description="Планируемые мероприятия (Markdown)")

    @validator("title")
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:  # noqa: N805
        """Проверяет, что название неисправности не пустое, если оно передано."""
        if v is None:
            return v
        return _normalize_title(v)


class FaultResponse(FaultBase):
    """Схема для ответа (с ID, статусом и датами)."""

    id: int
    status: StatusEnum
    created_at: datetime
    resolved_at: Optional[datetime] = None
    project: Optional[ProjectResponse] = None
    comments: List[CommentResponse] = []
    linked_knowledge: Optional[List[dict]] = None  # Связанные статьи
    parent_fault: Optional[dict] = None
    clones: Optional[List[dict]] = None

    class Config:
        """Конфигурация Pydantic-модели."""

        from_attributes = True
