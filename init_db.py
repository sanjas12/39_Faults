import os
import sys

# Добавляем корневую папку проекта в путь, чтобы Python мог найти модуль 'app'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import Base, engine

# Явно импортируем все модели, чтобы SQLAlchemy "увидел" их


def init_database():
    print("🚀 Начинаем создание таблиц...")
    try:
        # Создаём все таблицы, определённые в Base
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы успешно созданы!")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")


if __name__ == "__main__":
    init_database()
