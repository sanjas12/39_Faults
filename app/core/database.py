from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.database_url
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():  # type: ignore
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Импортируем все модели здесь, ПОСЛЕ определения Base, чтобы они
# зарегистрировались в Base.metadata. Это нужно делать в конце файла,
# чтобы избежать циклического импорта (all_models.py импортирует Base
# отсюда же). Любой модуль, импортирующий что-либо из database.py,
# теперь автоматически получает и все модели — Base.metadata.create_all()
# будет работать корректно в init_db.py, migrate_db.py, seed_data.py и т.д.
from app.models.all_models import Fault, Project, User, UserRole  # noqa: E402,F401
