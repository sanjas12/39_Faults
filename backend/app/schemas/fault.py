from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FaultBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "minor"
    project_id: Optional[int] = None


class FaultCreate(FaultBase):
    pass


class FaultResponse(FaultBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
