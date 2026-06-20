from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.all_models import Fault, Project
from app.schemas.fault import (
    FaultCreate,
    FaultResponse,
    FaultUpdate,
    SeverityEnum,
    StatusEnum,
)

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
    db: Session = Depends(get_db),
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

    # Поиск по названию
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(Fault.title.ilike(search_pattern))

    # Сортировка: сначала критические, потом по дате создания
    query = query.order_by(
        # Сортируем по важности (critical → major → minor → trivial)
        Fault.severity.desc(),
        Fault.created_at.desc(),
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
            detail=f"Неисправность с ID {fault_id} не найдена",
        )
    return fault


@router.patch(
    "/{fault_id}", response_model=FaultResponse, summary="Обновить неисправность"
)
def update_fault(
    fault_id: int, fault_update: FaultUpdate, db: Session = Depends(get_db)
):
    """
    Частичное обновление неисправности.
    """
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Неисправность с ID {fault_id} не найдена",
        )

    # Если меняем project_id, проверяем существование проекта
    if fault_update.project_id is not None and fault_update.project_id:
        project = (
            db.query(Project).filter(Project.id == fault_update.project_id).first()
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Проект с ID {fault_update.project_id} не найден",
            )
        # Если project_id = None, просто снимаем привязку

    # Обновляем только переданные поля
    update_data = fault_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fault, field, value)

    # Если статус стал "closed", устанавливаем resolved_at
    if fault_update.status == StatusEnum.CLOSED:
        fault.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(fault)
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
