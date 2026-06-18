from app.core.database import engine, Base
from app.models.all_models import Project, Fault

def migrate():
    print("🔄 Обновляем структуру БД...")
    
    # Этот способ создаст новые таблицы и добавит новые колонки
    # Но НЕ удалит существующие данные
    Base.metadata.create_all(bind=engine)
    
    print("✅ Структура БД обновлена!")

if __name__ == "__main__":
    migrate()