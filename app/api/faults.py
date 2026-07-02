import os
from pathlib import Path
import shutil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, Project, FaultHistory, User, KnowledgeBase, FaultAttachment
from app.schemas.fault import FaultCreate, FaultUpdate, FaultResponse, SeverityEnum, StatusEnum
from app.schemas.user import UserResponse
from app.services.email_service import email_service


router = APIRouter(prefix="/faults", tags=["faults"])


@router.post("/", response_model=FaultResponse, status_code=status.HTTP_201_CREATED, summary="Создать новую неисправность")
def create_fault(
    fault: FaultCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)  # ✅ Параметр должен быть здесь
):
    """Создание новой неисправности с отправкой уведомлений"""
    
    # Проверяем проект
    if fault.project_id:
        project = db.query(Project).filter(Project.id == fault.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Проект с ID {fault.project_id} не найден"
            )
    
    # Создаём неисправность
    db_fault = Fault(**fault.model_dump())
    db.add(db_fault)
    db.commit()
    db.refresh(db_fault)
    
    # ✅ Записываем в историю создание (используем current_user)
    try:
        log_history(
            db=db,
            fault_id=db_fault.id,
            event_type="creation",
            field="creation",
            old_value=None,
            new_value=f"Создана неисправность: {db_fault.title}",
            author=current_user.username  # ✅ current_user определён
        )
    except Exception as e:
        print(f"❌ Ошибка записи истории: {e}")
    
    # ✅ Отправляем уведомления
    try:
        # Получаем всех активных пользователей (кроме создателя)
        recipients = db.query(User).filter(
            User.id != current_user.id,
            User.is_active == True
        ).all()
        recipient_emails = [u.email for u in recipients if u.email]
        
        # Название проекта
        project_name = "Без проекта"
        if db_fault.project_id:
            project = db.query(Project).filter(Project.id == db_fault.project_id).first()
            if project:
                project_name = project.name
        
        if recipient_emails and email_service.enabled:
            email_service.send_fault_created(
                fault=db_fault,
                project_name=project_name,
                user_name=current_user.username,
                recipients=recipient_emails
            )
    except Exception as e:
        print(f"❌ Ошибка отправки уведомлений: {e}")
    

    # Записываем в историю создание
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


@router.get("/", response_model=List[FaultResponse], summary="Получить список неисправностей")
def list_faults(
    skip: int = Query(0, ge=0, description="Сколько пропустить"),
    limit: int = Query(100, ge=1, le=1000, description="Сколько вернуть"),
    status: Optional[StatusEnum] = Query(None, description="Фильтр по статусу"),
    severity: Optional[SeverityEnum] = Query(None, description="Фильтр по важности"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    project_id: Optional[int] = Query(None, description="Фильтр по проекту"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Получение списка неисправностей с фильтрацией и поиском.
    """
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
    
    # Поиск по названию (регистронезависимый)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                func.lower(Fault.title).like(func.lower(search_pattern)),
                func.lower(Fault.description).like(func.lower(search_pattern))
            )
        )
    
    # Сортировка
    query = query.order_by(
        Fault.severity.desc(),
        Fault.created_at.desc()
    )
    
    faults = query.offset(skip).limit(limit).all()
    
    # ✅ Формируем ответ вручную для каждого fault
    result = []
    for fault in faults:
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
        
        response_data = {
            "id": fault.id,
            "title": fault.title,
            "description": fault.description,
            "severity": fault.severity,
            "status": fault.status,
            "category": fault.category,
            "project_id": fault.project_id,
            "linked_knowledge_ids": fault.linked_knowledge_ids,
            "planned_actions": fault.planned_actions,
            "created_at": fault.created_at,
            "updated_at": fault.updated_at,
            "resolved_at": fault.resolved_at,
            "project": {
                "id": fault.project.id,
                "name": fault.project.name,
                "description": fault.project.description,
                "client": fault.project.client,
                "station": fault.project.station,
                "unit": fault.project.unit,
                "type": fault.project.type,
                "created_at": fault.project.created_at,
                "updated_at": fault.project.updated_at
            } if fault.project else None,
            "comments": [],
            "linked_knowledge": linked_knowledge,
            "parent_fault": {
                "id": fault.parent_fault.id,
                "title": fault.parent_fault.title,
                "severity": fault.parent_fault.severity,
                "status": fault.parent_fault.status
            } if fault.parent_fault else None,
            "clones": [
                {
                    "id": clone.id,
                    "title": clone.title,
                    "severity": clone.severity,
                    "status": clone.status
                }
                for clone in fault.clones
            ] if fault.clones else []
        }
        result.append(response_data)
    
    return result


@router.get("/{fault_id}", response_model=FaultResponse, summary="Получить неисправность по ID")
def get_fault(
    fault_id: int, 
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Получение детальной информации о неисправности.
    """
    fault = (
        db.query(Fault)
        .options(
            joinedload(Fault.project),
            joinedload(Fault.parent_fault),
            joinedload(Fault.clones)
        )
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
    
    # ✅ Формируем ответ вручную
    response_data = {
        "id": fault.id,
        "title": fault.title,
        "description": fault.description,
        "severity": fault.severity,
        "status": fault.status,
        "category": fault.category,
        "project_id": fault.project_id,
        "linked_knowledge_ids": fault.linked_knowledge_ids,
        "planned_actions": fault.planned_actions,
        "created_at": fault.created_at,
        "updated_at": fault.updated_at,
        "resolved_at": fault.resolved_at,
        "project": {
            "id": fault.project.id,
            "name": fault.project.name,
            "description": fault.project.description,
            "client": fault.project.client,
            "station": fault.project.station,
            "unit": fault.project.unit,
            "type": fault.project.type,
            "created_at": fault.project.created_at,
            "updated_at": fault.project.updated_at
        } if fault.project else None,
        "comments": [],
        "linked_knowledge": linked_knowledge,
        "parent_fault": {
            "id": fault.parent_fault.id,
            "title": fault.parent_fault.title,
            "severity": fault.parent_fault.severity,
            "status": fault.parent_fault.status
        } if fault.parent_fault else None,
        "clones": [
            {
                "id": clone.id,
                "title": clone.title,
                "severity": clone.severity,
                "status": clone.status
            }
            for clone in fault.clones
        ] if fault.clones else []
    }
    
    return response_data


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
        "category": fault.category or "",
        "project_id": fault.project_id,
        "parent_fault_id": fault.parent_fault_id,
        "linked_knowledge_ids": fault.linked_knowledge_ids or "",
        "planned_actions": fault.planned_actions or ""
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
    
    # Записываем историю
    author = current_user.username or "system"
    field_labels = {
        "title": "Название",
        "description": "Описание",
        "severity": "Важность",
        "status": "Статус",
        "category": "Категория",
        "project_id": "Проект",
        "parent_fault_id": "Родительская неисправность",
        "linked_knowledge_ids": "Связанные статьи",
        "planned_actions": "Планируемые мероприятия"
    }
    
    for field, old_value in old_values.items():
        new_value = getattr(fault, field, None)
        
        if field == "project_id":
            old_project = db.query(Project).filter(Project.id == old_value).first()
            new_project = db.query(Project).filter(Project.id == new_value).first()
            old_value_str = old_project.name if old_project else "Без проекта"
            new_value_str = new_project.name if new_project else "Без проекта"
        elif field == "parent_fault_id":
            old_parent = db.query(Fault).filter(Fault.id == old_value).first()
            new_parent = db.query(Fault).filter(Fault.id == new_value).first()
            old_value_str = f"#{old_parent.id} {old_parent.title}" if old_parent else "Нет"
            new_value_str = f"#{new_parent.id} {new_parent.title}" if new_parent else "Нет"
        elif field == "linked_knowledge_ids":
            old_ids = [int(id.strip()) for id in old_value.split(',') if id.strip()] if old_value else []
            new_ids = [int(id.strip()) for id in new_value.split(',') if id.strip()] if new_value else []
            
            old_articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(old_ids)).all() if old_ids else []
            new_articles = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(new_ids)).all() if new_ids else []
            
            old_value_str = ', '.join([a.title for a in old_articles]) if old_articles else "Нет статей"
            new_value_str = ', '.join([a.title for a in new_articles]) if new_articles else "Нет статей"
            
            for article in old_articles:
                if article.id not in new_ids:
                    article_fault_ids = [int(id.strip()) for id in article.related_faults.split(',') if id.strip()] if article.related_faults else []
                    if fault_id in article_fault_ids:
                        article_fault_ids.remove(fault_id)
                        article.related_faults = ','.join([str(id) for id in article_fault_ids]) if article_fault_ids else None
                        db.add(article)
            
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
    
    # ✅ Возвращаем правильно сериализованный ответ
    db.refresh(fault)
    
    fault_with_relations = db.query(Fault).options(
        joinedload(Fault.project),
        joinedload(Fault.parent_fault),
        joinedload(Fault.clones)
    ).filter(Fault.id == fault.id).first()
    
    response_data = {
        "id": fault_with_relations.id,
        "title": fault_with_relations.title,
        "description": fault_with_relations.description,
        "severity": fault_with_relations.severity,
        "status": fault_with_relations.status,
        "category": fault_with_relations.category,
        "project_id": fault_with_relations.project_id,
        "linked_knowledge_ids": fault_with_relations.linked_knowledge_ids,
        "planned_actions": fault_with_relations.planned_actions,
        "created_at": fault_with_relations.created_at,
        "updated_at": fault_with_relations.updated_at,
        "resolved_at": fault_with_relations.resolved_at,
        "project": {
            "id": fault_with_relations.project.id,
            "name": fault_with_relations.project.name,
            "description": fault_with_relations.project.description,
            "client": fault_with_relations.project.client,
            "station": fault_with_relations.project.station,
            "unit": fault_with_relations.project.unit,
            "type": fault_with_relations.project.type,
            "created_at": fault_with_relations.project.created_at,
            "updated_at": fault_with_relations.project.updated_at
        } if fault_with_relations.project else None,
        "comments": [],
        "linked_knowledge": [],
        "parent_fault": {
            "id": fault_with_relations.parent_fault.id,
            "title": fault_with_relations.parent_fault.title,
            "severity": fault_with_relations.parent_fault.severity,
            "status": fault_with_relations.parent_fault.status
        } if fault_with_relations.parent_fault else None,
        "clones": [
            {
                "id": clone.id,
                "title": clone.title,
                "severity": clone.severity,
                "status": clone.status
            }
            for clone in fault_with_relations.clones
        ] if fault_with_relations.clones else []
    }
    
    return response_data


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

@router.post("/{fault_id}/clone", response_model=FaultResponse, status_code=status.HTTP_201_CREATED)
def clone_fault(
    fault_id: int,
    target_project_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Клонировать неисправность в другой проект
    
    - Сохраняется название, описание, важность
    - Создаётся связь с родительской неисправностью
    - Копируются вложения (файлы)
    - Копируются связанные статьи
    - В истории отмечается клонирование
    """
    print(f"🔄 Клонирование неисправности #{fault_id} в проект #{target_project_id}")
    
    try:
        # 1. Находим исходную неисправность
        original_fault = db.query(Fault).options(
            joinedload(Fault.project)
        ).filter(Fault.id == fault_id).first()
        
        if not original_fault:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Исходная неисправность не найдена"
            )
        
        print(f"   📋 Исходная неисправность: #{original_fault.id} - {original_fault.title}")
        
        # 2. Проверяем целевой проект
        target_project = db.query(Project).filter(Project.id == target_project_id).first()
        if not target_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Целевой проект не найден"
            )
        
        print(f"   📁 Целевой проект: #{target_project.id} - {target_project.name}")
        
        # 3. Проверяем, что не клонируем в тот же проект
        if original_fault.project_id == target_project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя клонировать неисправность в тот же проект"
            )
        
        # 4. Создаём клон
        clone_fault_obj = Fault(
            title=f"[КЛОН] {original_fault.title}",
            description=original_fault.description,
            severity=original_fault.severity,
            status="open",
            project_id=target_project_id,
            parent_fault_id=original_fault.id,
            linked_knowledge_ids=original_fault.linked_knowledge_ids
        )
        
        db.add(clone_fault_obj)
        db.flush()
        print(f"   ✅ Клон создан: #{clone_fault_obj.id}")
        
        # 5. Копируем вложения
        attachments = db.query(FaultAttachment).filter(
            FaultAttachment.fault_id == original_fault.id
        ).all()
        
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        UPLOAD_DIR = BASE_DIR / "uploads"
        
        for attachment in attachments:
            try:
                old_path = Path(attachment.file_path)
                if old_path.exists():
                    clone_dir = UPLOAD_DIR / str(clone_fault_obj.id)
                    clone_dir.mkdir(exist_ok=True)
                    
                    new_filename = f"{current_user.username}_{attachment.filename}"
                    new_path = clone_dir / new_filename
                    
                    counter = 1
                    name, ext = os.path.splitext(new_filename)
                    while new_path.exists():
                        new_path = clone_dir / f"{name}_{counter}{ext}"
                        counter += 1
                    
                    shutil.copy2(old_path, new_path)
                    
                    new_attachment = FaultAttachment(
                        fault_id=clone_fault_obj.id,
                        filename=attachment.filename,
                        file_path=str(new_path),
                        file_size=attachment.file_size,
                        file_type=attachment.file_type,
                        description=attachment.description,
                        uploaded_by=current_user.username
                    )
                    db.add(new_attachment)
                    print(f"   📎 Скопировано вложение: {attachment.filename}")
            except Exception as e:
                print(f"   ⚠️ Ошибка копирования вложения {attachment.filename}: {e}")
        
        # 6. ✅ Записываем историю для клона
        log_history(
            db=db,
            fault_id=clone_fault_obj.id,
            event_type="creation",
            field="creation",
            old_value=None,
            new_value=f"Создан клон неисправности #{original_fault.id} из проекта '{original_fault.project.name if original_fault.project else 'Без проекта'}'",
            author=current_user.username
        )
        print(f"   📝 История для клона записана")
        
        # 7. ✅ Записываем историю для родительской неисправности
        log_history(
            db=db,
            fault_id=original_fault.id,
            event_type="field_change",
            field="Клонирование",
            old_value=None,
            new_value=f"Создан клон в проекте '{target_project.name}' (#{clone_fault_obj.id})",
            author=current_user.username
        )
        print(f"   📝 История для родителя записана")
        
        # 8. ✅ Записываем дополнительную информацию в историю клона
        # Информация о родителе
        log_history(
            db=db,
            fault_id=clone_fault_obj.id,
            event_type="field_change",
            field="Родительская неисправность",
            old_value=None,
            new_value=f"#{original_fault.id} {original_fault.title}",
            author=current_user.username
        )
        
        # Информация о целевом проекте
        log_history(
            db=db,
            fault_id=clone_fault_obj.id,
            event_type="field_change",
            field="Целевой проект",
            old_value=None,
            new_value=f"{target_project.name}",
            author=current_user.username
        )
        
        # 9. ✅ Если были скопированы вложения, записываем это в историю
        if attachments:
            log_history(
                db=db,
                fault_id=clone_fault_obj.id,
                event_type="field_change",
                field="Вложения",
                old_value=None,
                new_value=f"Скопировано {len(attachments)} файлов",
                author=current_user.username
            )
        
        # 10. ✅ Если были скопированы связанные статьи
        if original_fault.linked_knowledge_ids:
            log_history(
                db=db,
                fault_id=clone_fault_obj.id,
                event_type="field_change",
                field="Связанные статьи",
                old_value=None,
                new_value=f"Скопированы связанные статьи",
                author=current_user.username
            )
        
        db.commit()
        db.refresh(clone_fault_obj)
        
        # Загружаем связи для ответа
        clone_with_relations = db.query(Fault).options(
            joinedload(Fault.project),
            joinedload(Fault.parent_fault),
            joinedload(Fault.clones)
        ).filter(Fault.id == clone_fault_obj.id).first()
        
        # Формируем ответ
        response_data = {
            "id": clone_with_relations.id,
            "title": clone_with_relations.title,
            "description": clone_with_relations.description,
            "severity": clone_with_relations.severity,
            "status": clone_with_relations.status,
            "project_id": clone_with_relations.project_id,
            "linked_knowledge_ids": clone_with_relations.linked_knowledge_ids,
            "created_at": clone_with_relations.created_at,
            "resolved_at": clone_with_relations.resolved_at,
            "project": {
                "id": clone_with_relations.project.id,
                "name": clone_with_relations.project.name,
                "description": clone_with_relations.project.description,
                "client": clone_with_relations.project.client,
                "station": clone_with_relations.project.station,
                "unit": clone_with_relations.project.unit,
                "type": clone_with_relations.project.type,
                "created_at": clone_with_relations.project.created_at,
                "updated_at": clone_with_relations.project.updated_at
            } if clone_with_relations.project else None,
            "comments": [],
            "linked_knowledge": [],
            "parent_fault": {
                "id": clone_with_relations.parent_fault.id,
                "title": clone_with_relations.parent_fault.title,
                "severity": clone_with_relations.parent_fault.severity,
                "status": clone_with_relations.parent_fault.status
            } if clone_with_relations.parent_fault else None,
            "clones": [
                {
                    "id": clone.id,
                    "title": clone.title,
                    "severity": clone.severity,
                    "status": clone.status
                }
                for clone in clone_with_relations.clones
            ] if clone_with_relations.clones else []
        }
        
        print(f"✅ Клонирование завершено успешно! Новый ID: #{clone_fault_obj.id}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка при клонировании: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при клонировании: {str(e)}"
        )


@router.get("/categories/", response_model=List[str])
def get_categories(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список всех категорий неисправностей"""
    categories = db.query(Fault.category).distinct().all()
    return [c[0] for c in categories if c[0]]