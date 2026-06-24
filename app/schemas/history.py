from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class HistoryBase(BaseModel):
    fault_id: int
    event_type: str = "field_change"
    field: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    author: str = "system"

class HistoryCreate(HistoryBase):
    pass

class HistoryResponse(HistoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True