from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Project, ProjectHistory
from app.schemas.project_history import ProjectHistoryResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/projects/{project_id}/history", tags=["project_history"])

@router.get("/", response_model=List[ProjectHistoryResponse])
def get_project_history(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить историю изменений проекта"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    
    history = db.query(ProjectHistory).filter(
        ProjectHistory.project_id == project_id
    ).order_by(ProjectHistory.created_at.desc()).all()
    
    return history