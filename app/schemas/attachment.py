from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AttachmentBase(BaseModel):
    filename: str
    description: Optional[str] = None


class AttachmentCreate(AttachmentBase):
    fault_id: int
    file_path: str
    file_size: int
    file_type: Optional[str] = None
    uploaded_by: str = "system"


class AttachmentResponse(AttachmentBase):
    id: int
    fault_id: int
    file_path: str
    file_size: int
    file_type: Optional[str] = None
    uploaded_by: str
    created_at: datetime

    class Config:
        from_attributes = True
