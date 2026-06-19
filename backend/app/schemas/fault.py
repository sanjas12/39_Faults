from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum
from app.schemas.project import ProjectResponse
from app.schemas.comment import CommentResponse

class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"

class StatusEnum(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    CLOSED = "closed"

class FaultBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    severity: SeverityEnum = SeverityEnum.MINOR
    project_id: Optional[int] = Field(None, description="ID проекта (может быть null)")

    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Название неисправности не может быть пустым')
        return v.strip()

class FaultCreate(FaultBase):
    """Схема для создания неисправности"""
    pass

class FaultUpdate(BaseModel):
    """Схема для обновления неисправности (все поля опциональны)"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    severity: Optional[SeverityEnum] = None
    status: Optional[StatusEnum] = None
    project_id: Optional[int] = None
    
    @validator('title')
    def title_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Название неисправности не может быть пустым')
        return v.strip() if v else v

class FaultResponse(FaultBase):
    """Схема для ответа (с ID, статусом и датами)"""
    id: int
    status: StatusEnum
    created_at: datetime
    resolved_at: Optional[datetime] = None
    project: Optional[ProjectResponse] = None
    comments: List[CommentResponse] = []
    
    class Config:
        from_attributes = True