"""Точка входа FastAPI-приложения для системы учёта неисправностей (Faults)."""

from typing import Dict, Optional

from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware.auth import auth_middleware
from app.core.security import verify_password, create_access_token, decode_token
from app.core.database import SessionLocal
from app.models.all_models import User
from app.api import auth, comments, faults, projects, history, knowledge_base, project_history, backup, attachments
from app.services.scheduler import start_scheduler

from _version import __version__


app = FastAPI(
    title="Faults", description="Отслеживание неисправностей", version=__version__
)

# проблема с авторизаций, надо закоментировать
# app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

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
app.include_router(auth.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(knowledge_base.router, prefix="/api")
app.include_router(project_history.router, prefix="/api")
app.include_router(backup.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")


def is_authenticated(request: Request) -> bool:
    """Проверка авторизации пользователя"""
    # Проверяем токен в cookies
    token = request.cookies.get('access_token')
    if token:
        payload = decode_token(token)
        if payload:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == payload.get('sub')).first()
                if user and user.is_active:
                    request.state.user = user
                    return True
            finally:
                db.close()
    return False


def _render_page(
    request: Request,
    template_name: str,
    active_page: Optional[str] = None,
    **extra_context: object,
) -> HTMLResponse:
    """Отрендерить HTML-страницу через Jinja2Templates с проверкой авторизации
    Собирает базовый контекст (request, active_page) и добавляет
    дополнительные значения, специфичные для конкретной страницы.
    """
    
    # ✅ Проверяем авторизацию для всех страниц, кроме публичных
    public_pages = ['/login', '/register']
    
    # Проверяем, что запрос не на публичную страницу
    if request.url.path not in public_pages:
        if not is_authenticated(request):
            return RedirectResponse(url='/login', status_code=302)
    
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
    return {"status": "ok", "version": __version__}


@app.get("/kanban")
def kanban_page(request: Request) -> HTMLResponse:
    """Канбан-доска."""
    return _render_page(request, "kanban.html", active_page="kanban")


@app.get("/knowledge/{article_id}")
def knowledge_article_detail(request: Request, article_id: int):
    """Страница просмотра статьи"""
    return _render_page(request, "knowledge_article.html", active_page="knowledge", article_id=article_id)


@app.get("/settings")
def settings_page(request: Request):
    return _render_page(request, "settings.html", active_page="settings")


@app.get("/projects/{project_id}")
def project_detail(request: Request, project_id: int):
    """Детальная страница проекта"""
    return _render_page(request, "project_detail.html", active_page="projects", project_id=project_id)

if not app.debug:
    start_scheduler()


# ===== ПУБЛИЧНЫЕ СТРАНИЦЫ (без авторизации) =====
@app.get("/login")
def login_page(request: Request) -> HTMLResponse:
    """Страница входа в систему."""
    # Если пользователь уже авторизован, редиректим на дашборд
    if is_authenticated(request):
        return RedirectResponse(url='/', status_code=302)
    return _render_page(request, "login.html")

@app.get("/register")
def register_page(request: Request) -> HTMLResponse:
    """Страница регистрации."""
    # Если пользователь уже авторизован, редиректим на дашборд
    if is_authenticated(request):
        return RedirectResponse(url='/', status_code=302)
    return _render_page(request, "register.html")