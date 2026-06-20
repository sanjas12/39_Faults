from datetime import datetime

from pydantic import BaseModel


class CommentBase(BaseModel):
    content: str
    is_internal: bool = False


class CommentCreate(CommentBase):
    author: str = "system"


class CommentResponse(CommentBase):
    id: int
    fault_id: int
    author: str
    created_at: datetime

    class Config:
        from_attributes = True
