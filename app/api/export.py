from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, KnowledgeBase
from app.schemas.user import UserResponse
from app.services.pdf_service import generate_faults_pdf, generate_single_fault_pdf
from sqlalchemy import or_, func

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/faults/pdf")
def export_faults_pdf(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    severity: Optional[str] = Query(None, description="Фильтр по важности"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    project_id: Optional[int] = Query(None, description="Фильтр по проекту"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    limit: int = Query(100, ge=1, le=500, description="Максимальное количество записей"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Экспорт неисправностей в PDF
    """
    try:
        query = db.query(Fault).options(
            joinedload(Fault.project),
            joinedload(Fault.parent_fault),
            joinedload(Fault.clones)
        )
        
        # Фильтры
        if status:
            query = query.filter(Fault.status == status)
        if severity:
            query = query.filter(Fault.severity == severity)
        if category:
            query = query.filter(Fault.category == category)
        if project_id:
            query = query.filter(Fault.project_id == project_id)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    func.lower(Fault.title).like(func.lower(search_pattern)),
                    func.lower(Fault.description).like(func.lower(search_pattern))
                )
            )
        
        faults = query.order_by(Fault.created_at.desc()).limit(limit).all()
        
        if not faults:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Нет данных для экспорта"
            )
        
        # Преобразуем данные для PDF
        faults_data = []
        for fault in faults:
            try:
                # Загружаем проект
                project_data = None
                if fault.project:
                    project_data = {
                        "name": fault.project.name or "Без названия",
                        "client": fault.project.client or None
                    }
                
                # Загружаем связанные статьи
                linked_knowledge = []
                if fault.linked_knowledge_ids:
                    ids = [int(id.strip()) for id in fault.linked_knowledge_ids.split(',') if id.strip()]
                    if ids:
                        articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(ids)).all()
                        linked_knowledge = [
                            {"id": a.id, "title": a.title or "Без названия", "category": a.category or None}
                            for a in articles
                        ]
                
                # Родительская неисправность
                parent_data = None
                if fault.parent_fault:
                    parent_data = {
                        "id": fault.parent_fault.id,
                        "title": fault.parent_fault.title or "Без названия"
                    }
                
                # Клоны
                clones_data = []
                if fault.clones:
                    clones_data = [
                        {"id": c.id, "title": c.title or "Без названия"}
                        for c in fault.clones
                    ]
                
                faults_data.append({
                    "id": fault.id,
                    "title": fault.title or "Без названия",
                    "description": fault.description or "",
                    "severity": fault.severity or "не указана",
                    "status": fault.status or "не указан",
                    "category": fault.category or None,
                    "planned_actions": fault.planned_actions or "",
                    "created_at": fault.created_at.isoformat() if fault.created_at else None,
                    "updated_at": fault.updated_at.isoformat() if fault.updated_at else None,
                    "resolved_at": fault.resolved_at.isoformat() if fault.resolved_at else None,
                    "project": project_data,
                    "linked_knowledge": linked_knowledge,
                    "parent_fault": parent_data,
                    "clones": clones_data
                })
            except Exception as e:
                print(f"⚠️ Ошибка обработки неисправности #{fault.id}: {e}")
                continue
        
        if not faults_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Нет данных для экспорта"
            )
        
        # Генерируем PDF
        pdf_buffer = generate_faults_pdf(faults_data)
        
        # Формируем имя файла
        filename = f"faults_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка экспорта PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации PDF: {str(e)}"
        )


@router.get("/faults/{fault_id}/pdf")
def export_single_fault_pdf(
    fault_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Экспорт одной неисправности в PDF
    """
    try:
        fault = db.query(Fault).options(
            joinedload(Fault.project),
            joinedload(Fault.parent_fault),
            joinedload(Fault.clones)
        ).filter(Fault.id == fault_id).first()
        
        if not fault:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Неисправность не найдена"
            )
        
        # Загружаем проект
        project_data = None
        if fault.project:
            project_data = {
                "name": fault.project.name or "Без названия",
                "client": fault.project.client or None
            }
        
        # Загружаем связанные статьи
        linked_knowledge = []
        if fault.linked_knowledge_ids:
            ids = [int(id.strip()) for id in fault.linked_knowledge_ids.split(',') if id.strip()]
            if ids:
                articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(ids)).all()
                linked_knowledge = [
                    {"id": a.id, "title": a.title or "Без названия", "category": a.category or None}
                    for a in articles
                ]
        
        # Родительская неисправность
        parent_data = None
        if fault.parent_fault:
            parent_data = {
                "id": fault.parent_fault.id,
                "title": fault.parent_fault.title or "Без названия"
            }
        
        # Клоны
        clones_data = []
        if fault.clones:
            clones_data = [
                {"id": c.id, "title": c.title or "Без названия"}
                for c in fault.clones
            ]
        
        fault_data = {
            "id": fault.id,
            "title": fault.title or "Без названия",
            "description": fault.description or "",
            "severity": fault.severity or "не указана",
            "status": fault.status or "не указан",
            "category": fault.category or None,
            "planned_actions": fault.planned_actions or "",
            "created_at": fault.created_at.isoformat() if fault.created_at else None,
            "updated_at": fault.updated_at.isoformat() if fault.updated_at else None,
            "resolved_at": fault.resolved_at.isoformat() if fault.resolved_at else None,
            "project": project_data,
            "linked_knowledge": linked_knowledge,
            "parent_fault": parent_data,
            "clones": clones_data
        }
        
        pdf_buffer = generate_single_fault_pdf(fault_data)
        
        filename = f"fault_{fault_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка экспорта PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации PDF: {str(e)}"
        )