from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, KnowledgeBase
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post(
    "/", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED
)
def create_article(
    article: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Создать статью в базе знаний"""
    # ✅ Получаем данные и добавляем автора
    data = article.model_dump()
    data["author"] = current_user.username

    db_article = KnowledgeBase(**data)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


@router.get("/", response_model=List[KnowledgeBaseResponse])
def list_articles(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Поиск по названию и содержанию"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    tag: Optional[str] = Query(None, description="Фильтр по тегу"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Получить список статей"""
    query = db.query(KnowledgeBase)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                func.lower(KnowledgeBase.title).like(func.lower(search_pattern)),
                func.lower(KnowledgeBase.content).like(func.lower(search_pattern)),
            )
        )

    if category:
        query = query.filter(KnowledgeBase.category == category)

    if tag:
        query = query.filter(KnowledgeBase.tags.like(f"%{tag}%"))

    query = query.order_by(KnowledgeBase.created_at.desc())
    articles = query.offset(skip).limit(limit).all()

    # Добавляем связанные неисправности для каждой статьи
    result = []
    for article in articles:
        linked_faults = []
        if article.related_faults:
            ids = [
                int(id.strip())
                for id in article.related_faults.split(",")
                if id.strip()
            ]
            if ids:
                faults = db.query(Fault).filter(Fault.id.in_(ids)).all()
                linked_faults = [
                    {"id": f.id, "title": f.title, "status": f.status} for f in faults
                ]
        response = KnowledgeBaseResponse.model_validate(article)
        response.linked_faults = linked_faults
        result.append(response)

    return result


@router.get("/{article_id}", response_model=KnowledgeBaseResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Получить статью по ID с загрузкой связанных неисправностей"""
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )

    # Увеличиваем счётчик просмотров
    article.views += 1
    db.commit()
    db.refresh(article)

    # Загружаем связанные неисправности
    linked_faults = []
    if article.related_faults:
        ids = [
            int(id.strip()) for id in article.related_faults.split(",") if id.strip()
        ]
        if ids:
            faults = db.query(Fault).filter(Fault.id.in_(ids)).all()
            linked_faults = [
                {
                    "id": f.id,
                    "title": f.title,
                    "status": f.status,
                    "severity": f.severity,
                }
                for f in faults
            ]

    # Добавляем связанные неисправности в ответ
    response = KnowledgeBaseResponse.model_validate(article)
    response.linked_faults = linked_faults
    return response


@router.put("/{article_id}", response_model=KnowledgeBaseResponse)
def update_article(
    article_id: int,
    article_update: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Обновить статью с синхронизацией связанных неисправностей"""
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )

    # Сохраняем старые значения для синхронизации
    old_related_faults = article.related_faults or ""

    # Обновляем поля
    update_data = article_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)

    # ✅ Синхронизируем связанные неисправности
    if "related_faults" in update_data:
        old_ids = (
            [int(id.strip()) for id in old_related_faults.split(",") if id.strip()]
            if old_related_faults
            else []
        )
        new_ids = (
            [int(id.strip()) for id in article.related_faults.split(",") if id.strip()]
            if article.related_faults
            else []
        )

        # 1. Удаляем эту статью из старых неисправностей
        for fault_id in old_ids:
            if fault_id not in new_ids:
                fault = db.query(Fault).filter(Fault.id == fault_id).first()
                if fault:
                    fault_ids = (
                        [
                            int(id.strip())
                            for id in fault.linked_knowledge_ids.split(",")
                            if id.strip()
                        ]
                        if fault.linked_knowledge_ids
                        else []
                    )
                    if article_id in fault_ids:
                        fault_ids.remove(article_id)
                        fault.linked_knowledge_ids = (
                            ",".join([str(id) for id in fault_ids])
                            if fault_ids
                            else None
                        )
                        db.add(fault)

        # 2. Добавляем эту статью в новые неисправности
        for fault_id in new_ids:
            if fault_id not in old_ids:
                fault = db.query(Fault).filter(Fault.id == fault_id).first()
                if fault:
                    fault_ids = (
                        [
                            int(id.strip())
                            for id in fault.linked_knowledge_ids.split(",")
                            if id.strip()
                        ]
                        if fault.linked_knowledge_ids
                        else []
                    )
                    if article_id not in fault_ids:
                        fault_ids.append(article_id)
                        fault.linked_knowledge_ids = ",".join(
                            [str(id) for id in fault_ids]
                        )
                        db.add(fault)

        db.commit()

    # Загружаем связанные неисправности для ответа
    linked_faults = []
    if article.related_faults:
        ids = [
            int(id.strip()) for id in article.related_faults.split(",") if id.strip()
        ]
        if ids:
            faults = db.query(Fault).filter(Fault.id.in_(ids)).all()
            linked_faults = [
                {
                    "id": f.id,
                    "title": f.title,
                    "status": f.status,
                    "severity": f.severity,
                }
                for f in faults
            ]

    response = KnowledgeBaseResponse.model_validate(article)
    response.linked_faults = linked_faults
    return response


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Удалить статью"""
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )

    db.delete(article)
    db.commit()
    return None


@router.get("/categories/", response_model=List[str])
def get_categories(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Получить список всех категорий"""
    categories = db.query(KnowledgeBase.category).distinct().all()
    return [c[0] for c in categories if c[0]]


@router.get("/tags/", response_model=List[str])
def get_tags(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Получить список всех тегов"""
    articles = db.query(KnowledgeBase.tags).all()
    tags = set()
    for a in articles:
        if a[0]:
            for tag in a[0].split(","):
                tag = tag.strip()
                if tag:
                    tags.add(tag)
    return sorted(list(tags))
