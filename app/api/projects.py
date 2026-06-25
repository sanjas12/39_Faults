from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_engineer
from app.models.all_models import Fault, Project, ProjectHistory
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.user import UserResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый проект",
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_engineer),  # Только инженеры и админы
):
    """
    Создание нового проекта в системе.

    - **name**: Название проекта (обязательно)
    - **description**: Описание проекта (опционально)
    - **client**: Клиент-Заказчик (опционально)
    """
    # Проверяем, нет ли проекта с таким именем
    existing = db.query(Project).filter(Project.name == project.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Проект с названием '{project.name}' уже существует",
        )

    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

        # ✅ Записываем в историю создание проекта
    log_project_history(
        db=db,
        project_id=db_project.id,
        event_type="creation",
        field="creation",
        old_value=None,
        new_value=f"Создан проект: {db_project.name}",
        author=current_user.username
    )

    return db_project


@router.get(
    "/", response_model=List[ProjectResponse], summary="Получить список проектов"
)
def list_projects(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Поиск по названию или клиенту"),
    station: Optional[str] = Query(None, description="Фильтр по станции"),      # ✅ Добавляем
    unit: Optional[int] = Query(None, description="Фильтр по номеру блока"),    # ✅ Добавляем
    type: Optional[str] = Query(None, description="Фильтр по типу проекта"),    # ✅ Добавляем
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список проектов с фильтрацией"""
    query = db.query(Project)
    
    # ✅ Фильтр по станции
    if station:
        query = query.filter(Project.station == station)
    
    # ✅ Фильтр по номеру блока
    if unit is not None:
        query = query.filter(Project.unit == unit)
    
    # ✅ Фильтр по типу
    if type:
        query = query.filter(Project.type == type)
    
    # Поиск по названию или клиенту
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                func.lower(Project.name).like(func.lower(search_pattern)),
                func.lower(Project.client).like(func.lower(search_pattern))
            )
        )
    
    projects = query.offset(skip).limit(limit).all()
    return projects


@router.get(
    "/{project_id}", response_model=ProjectResponse, summary="Получить проект по ID"
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),  # Все авторизованные
):
    """
    Получение детальной информации о проекте по его ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден",
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_engineer)
):
    """Обновить проект с записью в историю"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден"
        )
    
    # Сохраняем старые значения
    old_values = {
        "name": project.name,
        "description": project.description or "",
        "client": project.client or "",
        "station": project.station or "",  # ✅ Добавляем
        "unit": project.unit,
        "type": project.type or ""
    }
    
    # Проверяем имя
    if project_update.name:
        existing = db.query(Project).filter(
            Project.name == project_update.name,
            Project.id != project_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Проект с названием '{project_update.name}' уже существует"
            )
    
    # Обновляем поля
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    # Записываем историю изменений
    author = current_user.username or "system"
    field_labels = {
        "name": "Название",
        "description": "Описание",
        "client": "Клиент",
        "station": "Станция",      # ✅ Добавляем
        "unit": "Блок",
        "type": "Тип"
    }
    
    for field, old_value in old_values.items():
        new_value = getattr(project, field, None)
        old_value_str = str(old_value) if old_value is not None else ""
        new_value_str = str(new_value) if new_value is not None else ""
        
        if old_value_str != new_value_str:
            log_project_history(
                db=db,
                project_id=project.id,
                event_type="field_change",
                field=field_labels.get(field, field),
                old_value=old_value_str or "пусто",
                new_value=new_value_str or "пусто",
                author=author
            )
    
    return project


@router.delete(
    "/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить проект"
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_engineer),  # Только инженеры и админы
):
    """
    Удаление проекта по ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден",
        )

    # Здесь можно добавить проверку на наличие связанных неисправностей
    # if project.faults:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Нельзя удалить проект, у которого есть неисправности"
    #     )

    db.delete(project)
    db.commit()
    return None


@router.get(
    "/{project_id}/stats", summary="Получить статистику по неисправностям проекта"
)
def get_project_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),  # Все авторизованные
):
    """
    Получение статистики по неисправностям для проекта.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден",
        )

    faults = db.query(Fault).filter(Fault.project_id == project_id).all()

    stats = {
        "project_id": project_id,
        "project_name": project.name,
        "total": len(faults),
        "by_status": {
            "open": sum(1 for f in faults if f.status == "open"),
            "in_progress": sum(1 for f in faults if f.status == "in_progress"),
            "review": sum(1 for f in faults if f.status == "review"),
            "closed": sum(1 for f in faults if f.status == "closed"),
        },
        "by_severity": {
            "critical": sum(1 for f in faults if f.severity == "critical"),
            "major": sum(1 for f in faults if f.severity == "major"),
            "minor": sum(1 for f in faults if f.severity == "minor"),
            "trivial": sum(1 for f in faults if f.severity == "trivial"),
        },
    }

    return stats

@router.get("/stations/", response_model=List[str])
def get_stations(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список всех станций"""
    stations = db.query(Project.station).distinct().all()
    return [s[0] for s in stations if s[0]]


@router.get("/types/", response_model=List[str])
def get_types(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список всех типов проектов"""
    types = db.query(Project.type).distinct().all()
    return [t[0] for t in types if t[0]]


@router.get("/units/", response_model=List[int])
def get_units(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список всех номеров блоков"""
    units = db.query(Project.unit).distinct().all()
    return [u[0] for u in units if u[0] is not None]


def log_project_history(
    db: Session,
    project_id: int,
    event_type: str,
    field: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    author: str = "system"
):
    """Запись события в историю проекта"""
    history = ProjectHistory(
        project_id=project_id,
        event_type=event_type,
        field=field,
        old_value=old_value,
        new_value=new_value,
        author=author
    )
    db.add(history)
    db.commit()


    