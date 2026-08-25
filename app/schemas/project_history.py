from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectHistoryBase(BaseModel):
    project_id: int
    event_type: str = "field_change"
    field: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    author: str = "system"


class ProjectHistoryCreate(ProjectHistoryBase):
    pass


class ProjectHistoryResponse(ProjectHistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
