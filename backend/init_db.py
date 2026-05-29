# разово запустить скрипт для инициализации БД
# uv run python init_db.py


from app.core.database import Base, engine


def init():
    print("Создаём таблицы...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы!")


if __name__ == "__main__":
    init()
