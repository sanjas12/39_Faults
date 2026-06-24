"""Точка входа FastAPI-приложения для системы учёта неисправностей (Faults)."""

from typing import Dict, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware.auth import auth_middleware
from fastapi import Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.core.security import verify_password, create_access_token
from app.models.all_models import User

from _version import __version__
from app.api import auth, comments, faults, projects, history, knowledge_base

app = FastAPI(
    title="Faults", description="Отслеживание неисправностей", version=__version__
)

app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

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
    return {"status": "ok", "version": __version__}


@app.get("/kanban")
def kanban_page(request: Request) -> HTMLResponse:
    """Канбан-доска."""
    return _render_page(request, "kanban.html", active_page="kanban")


@app.get("/login")
def login_page(request: Request) -> HTMLResponse:
    """Страница входа в систему."""
    return _render_page(request, "login.html")

@app.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Обработка POST-запроса для входа"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Неверное имя пользователя или пароль"
            })
        
        if not user.is_active:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Пользователь заблокирован"
            })
        
        # Создаём токен
        token = create_access_token({"sub": user.username, "role": user.role})
        
        # Устанавливаем cookie и редиректим
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="access_token", value=token, httponly=True)
        return response
    finally:
        db.close()

@app.get("/register")
def register_page(request: Request) -> HTMLResponse:
    """Страница регистрации."""
    return _render_page(request, "register.html")