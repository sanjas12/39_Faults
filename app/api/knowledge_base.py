from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import KnowledgeBase
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    article: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Создать статью в базе знаний"""
    # ✅ Получаем данные и добавляем автора
    data = article.model_dump()
    data['author'] = current_user.username
    
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
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список статей"""
    query = db.query(KnowledgeBase)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                func.lower(KnowledgeBase.title).like(func.lower(search_pattern)),
                func.lower(KnowledgeBase.content).like(func.lower(search_pattern))
            )
        )
    
    if category:
        query = query.filter(KnowledgeBase.category == category)
    
    if tag:
        query = query.filter(KnowledgeBase.tags.like(f"%{tag}%"))
    
    query = query.order_by(KnowledgeBase.created_at.desc())
    articles = query.offset(skip).limit(limit).all()
    return articles

@router.get("/{article_id}", response_model=KnowledgeBaseResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить статью по ID"""
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена"
        )
    
    # Увеличиваем счётчик просмотров
    article.views += 1
    db.commit()
    db.refresh(article)
    
    return article

@router.put("/{article_id}", response_model=KnowledgeBaseResponse)
def update_article(
    article_id: int,
    article_update: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Обновить статью"""
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена"
        )
    
    update_data = article_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)
    
    db.commit()
    db.refresh(article)
    return article

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Удалить статью"""
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статья не найдена"
        )
    
    db.delete(article)
    db.commit()
    return None

@router.get("/categories/", response_model=List[str])
def get_categories(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список всех категорий"""
    categories = db.query(KnowledgeBase.category).distinct().all()
    return [c[0] for c in categories if c[0]]

@router.get("/tags/", response_model=List[str])
def get_tags(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список всех тегов"""
    articles = db.query(KnowledgeBase.tags).all()
    tags = set()
    for a in articles:
        if a[0]:
            for tag in a[0].split(','):
                tag = tag.strip()
                if tag:
                    tags.add(tag)
    return sorted(list(tags))