from app.core.database import engine, Base
from app.models.all_models import Project, Fault

def migrate():
    print("🔄 Обновляем структуру БД...")
    
    # Этот способ сработает для добавления новых колонок
    # ВНИМАНИЕ: для сложных изменений используйте Alembic
    Base.metadata.create_all(bind=engine)
    
    print("✅ Структура БД обновлена!")

if __name__ == "__main__":
    migrate()