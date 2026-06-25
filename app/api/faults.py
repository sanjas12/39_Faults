from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, Project, FaultHistory, KnowledgeBase
from app.schemas.fault import (
    FaultCreate,
    FaultResponse,
    FaultUpdate,
    SeverityEnum,
    StatusEnum,
)
from app.schemas.user import UserResponse 


router = APIRouter(prefix="/faults", tags=["faults"])


@router.post(
    "/",
    response_model=FaultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую неисправность",
)
def create_fault(fault: FaultCreate, db: Session = Depends(get_db)):
    """
    Создание новой неисправности.

    - **title**: Название неисправности (обязательно)
    - **description**: Описание (опционально)
    - **severity**: Важность (critical, major, minor, trivial)
    - **project_id**: ID проекта (опционально)
    """
    # Если указан project_id, проверяем существование проекта
    if fault.project_id:
        project = db.query(Project).filter(Project.id == fault.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Проект с ID {fault.project_id} не найден",
            )
    
    db_fault = Fault(**fault.model_dump())
    db.add(db_fault)
    db.commit()
    db.refresh(db_fault)
    
    # ✅ Записываем в историю создание
    log_history(
        db=db,
        fault_id=db_fault.id,
        event_type="creation",
        field="creation",
        old_value=None,
        new_value=f"Создана неисправность: {db_fault.title}",
        author=current_user.username
    )
    
    return db_fault


@router.get(
    "/", response_model=List[FaultResponse], summary="Получить список неисправностей"
)
def list_faults(
    skip: int = Query(0, ge=0, description="Сколько пропустить"),
    limit: int = Query(100, ge=1, le=1000, description="Сколько вернуть"),
    status: Optional[StatusEnum] = Query(None, description="Фильтр по статусу"),
    severity: Optional[SeverityEnum] = Query(None, description="Фильтр по важности"),
    project_id: Optional[int] = Query(None, description="Фильтр по проекту"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    db: Session = Depends(get_db)
):
    """
    Получение списка неисправностей с фильтрацией и поиском.
    """
    # Подгружаем связанный проект
    query = db.query(Fault).options(joinedload(Fault.project))
    
    # Фильтры
    if status:
        query = query.filter(Fault.status == status)
    if severity:
        query = query.filter(Fault.severity == severity)
    if project_id:
        query = query.filter(Fault.project_id == project_id)
    
    # ✅ Поиск по названию (регистронезависимый)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                func.lower(Fault.title).like(func.lower(search_pattern)),
                func.lower(Fault.description).like(func.lower(search_pattern))
            )
        )
    
    # Сортировка: сначала критические, потом по дате создания
    query = query.order_by(
        # Сортируем по важности (critical → major → minor → trivial)
        Fault.severity.desc(),
        Fault.created_at.desc()
    )
    
    faults = query.offset(skip).limit(limit).all()
    return faults


@router.get(
    "/{fault_id}", response_model=FaultResponse, summary="Получить неисправность по ID"
)
def get_fault(fault_id: int, db: Session = Depends(get_db)):
    """
    Получение детальной информации о неисправности.
    """
    fault = (
        db.query(Fault)
        .options(joinedload(Fault.project))
        .filter(Fault.id == fault_id)
        .first()
    )
    if not fault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Неисправность с ID {fault_id} не найдена"
        )
    
    # Загружаем связанные статьи
    linked_knowledge = []
    if fault.linked_knowledge_ids:
        ids = [int(id.strip()) for id in fault.linked_knowledge_ids.split(',') if id.strip()]
        if ids:
            articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(ids)).all()
            linked_knowledge = [
                {
                    "id": a.id,
                    "title": a.title,
                    "category": a.category,
                    "tags": a.tags
                }
                for a in articles
            ]
    
    # Добавляем связанные статьи в ответ
    response = FaultResponse.model_validate(fault)
    response.linked_knowledge = linked_knowledge
    return response


@router.patch("/{fault_id}", response_model=FaultResponse)
def update_fault(
    fault_id: int,
    fault_update: FaultUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Частичное обновление неисправности с записью в историю"""
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Неисправность с ID {fault_id} не найдена"
        )
    
    # Сохраняем старые значения
    old_values = {
        "title": fault.title,
        "description": fault.description or "",
        "severity": fault.severity,
        "status": fault.status,
        "project_id": fault.project_id,
        "linked_knowledge_ids": fault.linked_knowledge_ids or ""
    }
    
    # Проверяем project_id
    if fault_update.project_id is not None:
        if fault_update.project_id:
            project = db.query(Project).filter(Project.id == fault_update.project_id).first()
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Проект с ID {fault_update.project_id} не найден"
                )
    
    # Обновляем поля
    update_data = fault_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fault, field, value)
    
    if fault_update.status == StatusEnum.CLOSED:
        fault.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(fault)
    
    # ✅ Записываем историю и обновляем связанные статьи
    author = current_user.username or "system"
    field_labels = {
        "title": "Название",
        "description": "Описание",
        "severity": "Важность",
        "status": "Статус",
        "project_id": "Проект",
        "linked_knowledge_ids": "Связанные статьи"
    }
    
    for field, old_value in old_values.items():
        new_value = getattr(fault, field, None)
        
        if field == "project_id":
            old_project = db.query(Project).filter(Project.id == old_value).first()
            new_project = db.query(Project).filter(Project.id == new_value).first()
            old_value_str = old_project.name if old_project else "Без проекта"
            new_value_str = new_project.name if new_project else "Без проекта"
        elif field == "linked_knowledge_ids":
            # ✅ Обновляем связанные статьи
            old_ids = [int(id.strip()) for id in old_value.split(',') if id.strip()] if old_value else []
            new_ids = [int(id.strip()) for id in new_value.split(',') if id.strip()] if new_value else []
            
            # Получаем названия статей
            old_articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(old_ids)).all() if old_ids else []
            new_articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(new_ids)).all() if new_ids else []
            
            old_value_str = ', '.join([a.title for a in old_articles]) if old_articles else "Нет статей"
            new_value_str = ', '.join([a.title for a in new_articles]) if new_articles else "Нет статей"
            
            # ✅ Обновляем related_faults в статьях
            # 1. Удаляем эту неисправность из старых статей
            for article in old_articles:
                if article.id not in new_ids:
                    article_fault_ids = [int(id.strip()) for id in article.related_faults.split(',') if id.strip()] if article.related_faults else []
                    if fault_id in article_fault_ids:
                        article_fault_ids.remove(fault_id)
                        article.related_faults = ','.join([str(id) for id in article_fault_ids]) if article_fault_ids else None
                        db.add(article)
            
            # 2. Добавляем эту неисправность в новые статьи
            for article in new_articles:
                if article.id not in old_ids:
                    article_fault_ids = [int(id.strip()) for id in article.related_faults.split(',') if id.strip()] if article.related_faults else []
                    if fault_id not in article_fault_ids:
                        article_fault_ids.append(fault_id)
                        article.related_faults = ','.join([str(id) for id in article_fault_ids])
                        db.add(article)
            
            db.commit()
        else:
            old_value_str = str(old_value) if old_value is not None else ""
            new_value_str = str(new_value) if new_value is not None else ""
        
        if old_value_str != new_value_str:
            log_history(
                db=db,
                fault_id=fault.id,
                event_type="field_change",
                field=field_labels.get(field, field),
                old_value=old_value_str,
                new_value=new_value_str,
                author=author
            )
    
    # В функции update_fault, после обновления связанных статей:

    # ✅ Записываем в историю изменения связанных статей
    if field == "linked_knowledge_ids" and old_value_str != new_value_str:
        # Дополнительная запись в историю для каждой привязанной/отвязанной статьи
        old_ids = [int(id.strip()) for id in old_value.split(',') if id.strip()] if old_value else []
        new_ids = [int(id.strip()) for id in new_value.split(',') if id.strip()] if new_value else []
        
        added_ids = [id for id in new_ids if id not in old_ids]
        removed_ids = [id for id in old_ids if id not in new_ids]
        
        if added_ids:
            added_articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(added_ids)).all()
            for article in added_articles:
                log_history(
                    db=db,
                    fault_id=fault.id,
                    event_type="field_change",
                    field="Привязана статья",
                    old_value=None,
                    new_value=article.title,
                    author=author
                )
        
        if removed_ids:
            removed_articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(removed_ids)).all()
            for article in removed_articles:
                log_history(
                    db=db,
                    fault_id=fault.id,
                    event_type="field_change",
                    field="Отвязана статья",
                    old_value=article.title,
                    new_value=None,
                    author=author
                )
    
    return fault


@router.delete(
    "/{fault_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить неисправность",
)
def delete_fault(fault_id: int, db: Session = Depends(get_db)):
    """
    Удаление неисправности по ID.
    """
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Неисправность с ID {fault_id} не найдена",
        )

    db.delete(fault)
    db.commit()
    return None


@router.get(
    "/project/{project_id}",
    response_model=List[FaultResponse],
    summary="Получить все неисправности проекта",
)
def get_faults_by_project(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Получение всех неисправностей для конкретного проекта.
    """
    # Проверяем существование проекта
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден",
        )

    faults = (
        db.query(Fault)
        .options(joinedload(Fault.project))
        .filter(Fault.project_id == project_id)
        .order_by(Fault.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return faults


def log_history(
    db: Session,
    fault_id: int,
    event_type: str,  # field_change, creation, comment
    field: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    author: str = "system"
):
    """Запись события в историю"""
    try:
        history = FaultHistory(
            fault_id=fault_id,
            event_type=event_type,
            field=field,
            old_value=old_value,
            new_value=new_value,
            author=author
        )
        db.add(history)
        db.commit()
        print(f"✅ История записана: {event_type} - {field} - {old_value} -> {new_value}")
    except Exception as e:
        print(f"❌ Ошибка записи истории: {e}")
        db.rollback()