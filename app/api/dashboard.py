from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, Project, FaultAttachment, KnowledgeBase, FaultHistory
from app.schemas.user import UserResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Получение статистики для дашборда (оптимизировано)
    """
    # Основная статистика
    total_faults = db.query(Fault).count()
    critical_faults = db.query(Fault).filter(Fault.severity == "critical").count()
    in_progress_faults = db.query(Fault).filter(Fault.status == "in_progress").count()
    closed_faults = db.query(Fault).filter(Fault.status == "closed").count()
    
    # С планируемыми мероприятиями
    faults_with_actions = db.query(Fault).filter(
        Fault.planned_actions.isnot(None),
        Fault.planned_actions != ""
    ).count()
    
    # Количество неисправностей с вложениями
    faults_with_attachments = db.query(FaultAttachment.fault_id).distinct().count()
    
    # Количество клонов
    clones_count = db.query(Fault).filter(Fault.parent_fault_id.isnot(None)).count()
    
    # Количество статей в БЗ
    total_knowledge = db.query(KnowledgeBase).count()
    
    # Список проектов с количеством неисправностей (топ-5)
    projects_stats = db.query(
        Project.id,
        Project.name,
        Project.client,
        func.count(Fault.id).label('faults_count')
    ).outerjoin(Fault, Fault.project_id == Project.id)\
     .group_by(Project.id)\
     .order_by(func.count(Fault.id).desc())\
     .limit(5).all()
    
    projects_list = [
        {
            "id": p.id,
            "name": p.name,
            "client": p.client,
            "faults_count": p.faults_count
        }
        for p in projects_stats
    ]
    
    # ✅ Последние 5 изменённых неисправностей (исправлено для SQLite)
    # Используем ORDER BY с CASE для SQLite
    recent_faults = db.query(Fault).options(
        joinedload(Fault.project)
    ).order_by(
        # В SQLite используем CASE вместо COALESCE
        case(
            (Fault.updated_at.isnot(None), Fault.updated_at),
            else_=Fault.created_at
        ).desc()
    ).limit(5).all()
    
    recent_faults_list = []
    for fault in recent_faults:
        # Загружаем проект (если есть)
        project_name = None
        if fault.project:
            project_name = fault.project.name
        elif fault.project_id:
            project = db.query(Project).filter(Project.id == fault.project_id).first()
            if project:
                project_name = project.name
        
        recent_faults_list.append({
            "id": fault.id,
            "title": fault.title,
            "severity": fault.severity,
            "status": fault.status,
            "category": fault.category,
            "planned_actions": fault.planned_actions,
            "project_name": project_name or "Без проекта",
            "updated_at": fault.updated_at.isoformat() if fault.updated_at else fault.created_at.isoformat()
        })
    
    return {
        "stats": {
            "total": total_faults,
            "critical": critical_faults,
            "in_progress": in_progress_faults,
            "closed": closed_faults,
            "with_actions": faults_with_actions,
            "with_attachments": faults_with_attachments,
            "clones": clones_count,
            "knowledge": total_knowledge
        },
        "projects": projects_list,
        "recent_faults": recent_faults_list
    }