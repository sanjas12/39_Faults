from backend._version import __version__
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Faults", description="Отслеживание неисправностей", version=__version__
)

# CORS для React (будет работать на разных портах)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev сервер
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Faults API работает"}


@app.get("/health")
def health():
    return {"status": "ok", "python_version": "3.8.10"}
