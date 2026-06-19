from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.api import faults, projects

from _version import __version__

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

# HTML страницы
@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard"
    })

@app.get("/projects")
def projects_page(request: Request):
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "active_page": "projects"
    })

@app.get("/faults")
def faults_page(request: Request):
    return templates.TemplateResponse("faults.html", {
        "request": request,
        "active_page": "faults"
    })

@app.get("/knowledge")
def knowledge_page(request: Request):
    return templates.TemplateResponse("knowledge_base.html", {
        "request": request,
        "active_page": "knowledge"
    })

@app.get("/faults/{fault_id}")
def fault_detail(request: Request, fault_id: int):
    return templates.TemplateResponse("fault_detail.html", {
        "request": request,
        "fault_id": fault_id,
        "active_page": "faults"
    })

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}