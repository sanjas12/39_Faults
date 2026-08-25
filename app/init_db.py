from app.core.database import Base, engine


def init_database():
    """Создание всех таблиц в базе данных"""
    print("🔄 Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы!")


if __name__ == "__main__":
    init_database()
