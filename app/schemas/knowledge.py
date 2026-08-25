from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class KnowledgeBaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tags: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    related_faults: Optional[str] = Field(None, max_length=500)
    is_published: bool = True


class KnowledgeBaseCreate(KnowledgeBaseBase):
    # ✅ Убираем author, он будет добавлен на бэкенде
    pass


class KnowledgeBaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    related_faults: Optional[str] = Field(None, max_length=500)
    is_published: Optional[bool] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    author: str
    views: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    linked_faults: Optional[List[dict]] = None

    class Config:
        from_attributes = True
