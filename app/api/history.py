from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, FaultHistory
from app.schemas.history import HistoryResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/faults/{fault_id}/history", tags=["history"])

@router.get("/", response_model=List[HistoryResponse])
def get_fault_history(
    fault_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить историю изменений неисправности"""
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Неисправность не найдена")
    
    history = db.query(FaultHistory).filter(
        FaultHistory.fault_id == fault_id
    ).order_by(FaultHistory.created_at.desc()).all()
    
    return history