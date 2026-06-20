"""Точка входа FastAPI-приложения для системы учёта неисправностей (Faults)."""

from typing import Dict, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from _version import __version__
from app.api import auth, comments, faults, projects

app = FastAPI(
    title="Faults", description="Отслеживание неисправностей", version=__version__
)

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# CORS (для API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роутеры
app.include_router(faults.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(auth.router)


def _render_page(
    request: Request,
    template_name: str,
    active_page: Optional[str] = None,
    **extra_context: object,
) -> HTMLResponse:
    """Отрендерить HTML-страницу через Jinja2Templates.

    Собирает базовый контекст (request, active_page) и добавляет
    дополнительные значения, специфичные для конкретной страницы.
    """
    context: Dict[str, object] = {"request": request}
    if active_page is not None:
        context["active_page"] = active_page
    context.update(extra_context)
    return templates.TemplateResponse(template_name, context)


# HTML страницы
@app.get("/")
def dashboard(request: Request) -> HTMLResponse:
    """Главная панель (дашборд)."""
    return _render_page(request, "dashboard.html", active_page="dashboard")


@app.get("/projects")
def projects_page(request: Request) -> HTMLResponse:
    """Страница со списком проектов."""
    return _render_page(request, "projects.html", active_page="projects")


@app.get("/faults")
def faults_page(request: Request) -> HTMLResponse:
    """Страница со списком неисправностей."""
    return _render_page(request, "faults.html", active_page="faults")


@app.get("/knowledge")
def knowledge_page(request: Request) -> HTMLResponse:
    """Страница базы знаний."""
    return _render_page(request, "knowledge_base.html", active_page="knowledge")


@app.get("/faults/{fault_id}")
def fault_detail(request: Request, fault_id: int) -> HTMLResponse:
    """Детальная карточка конкретной неисправности."""
    return _render_page(
        request, "fault_detail.html", active_page="faults", fault_id=fault_id
    )


@app.get("/health")
def health() -> Dict[str, str]:
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/kanban")
def kanban_page(request: Request) -> HTMLResponse:
    """Канбан-доска."""
    return _render_page(request, "kanban.html", active_page="kanban")


@app.get("/login")
def login_page(request: Request) -> HTMLResponse:
    """Страница входа в систему."""
    return _render_page(request, "login.html")
