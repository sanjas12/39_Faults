from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_engineer, require_admin
from app.models.all_models import Project, Fault
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый проект"
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_engineer)  # Только инженеры и админы
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
            detail=f"Проект с названием '{project.name}' уже существует"
        )
    
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get(
    "/",
    response_model=List[ProjectResponse],
    summary="Получить список проектов"
)
def list_projects(
    skip: int = Query(0, ge=0, description="Сколько пропустить"),
    limit: int = Query(100, ge=1, le=1000, description="Сколько вернуть"),
    search: Optional[str] = Query(None, description="Поиск по названию или клиенту"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)  # Все авторизованные
):
    """
    Получение списка проектов с возможностью поиска и пагинации.
    """
    query = db.query(Project)
    
    # Поиск по названию или клиенту
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Project.name.ilike(search_pattern),
                Project.client.ilike(search_pattern)
            )
        )
    
    # Сортировка по дате создания (новые сверху)
    query = query.order_by(Project.created_at.desc())
    
    projects = query.offset(skip).limit(limit).all()
    return projects

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Получить проект по ID"
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)  # Все авторизованные
):
    """
    Получение детальной информации о проекте по его ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден"
        )
    return project

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Полностью обновить проект"
)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Полное обновление проекта. Все поля обязательны.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден"
        )
    
    # Проверяем, не занято ли имя другим проектом
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
    
    # Обновляем только переданные поля
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить проект"
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(require_engineer)  # Только инженеры и админы
):
    """
    Удаление проекта по ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден"
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
    "/{project_id}/stats",
    summary="Получить статистику по неисправностям проекта"
)
def get_project_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)  # Все авторизованные
):
    """
    Получение статистики по неисправностям для проекта.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Проект с ID {project_id} не найден"
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
        }
    }
    
    return stats