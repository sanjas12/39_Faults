from .attachments import router as attachments_router
from .auth import router as auth_router
from .backup import router as backup_router
from .comments import router as comments_router
from .dashboard import router as dashboard_router  # ✅ Должен быть
from .export import router as export_router
from .faults import router as faults_router
from .history import router as history_router
from .knowledge_base import router as knowledge_base_router
from .project_history import router as project_history_router
from .projects import router as projects_router

__all__ = [
    "attachments_router",
    "auth_router",
    "backup_router",
    "comments_router",
    "dashboard_router",
    "export_router",
    "faults_router",
    "history_router",
    "knowledge_base_router",
    "project_history_router",
    "projects_router",
]
