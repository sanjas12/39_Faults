from app.core.database import Base, engine

# Явно импортируем все модели, чтобы SQLAlchemy "увидел" их и зарегистрировал
# их таблицы в Base.metadata. Без этого create_all() ничего не создаст.
from app.models.all_models import Fault, Project, User, UserRole  # noqa: F401


def migrate():
    print("🔄 Обновляем структуру БД...")

    # Этот способ создаст новые таблицы и добавит новые колонки
    # Но НЕ удалит существующие данные
    Base.metadata.create_all(bind=engine)

    print("✅ Структура БД обновлена!")


if __name__ == "__main__":
    migrate()
