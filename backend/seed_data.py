from app.core.database import SessionLocal
from app.models.all_models import Project

def seed_projects():
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже проекты
        if db.query(Project).count() > 0:
            print("📦 Проекты уже есть в БД")
            return
        
        projects = [
            Project(
                name="Кольская_САРЗ_1",
                description="Модернизация системы управления котлами",
                client="Кольская",
                unit=1,
                type="САРЗ"
            ),
            Project(
                name="Кольская_САРЗ_2",
                description="Внедрение системы диспетчерского контроля",
                client="Кольская",
                unit=2,
                type="САРЗ"
            ),
            Project(
                name="Смоленская_САРЗ_2",
                description="Система автоматического управления дизель-генератора",
                client="Смоленская",
                unit=2,
                type="САРЗ"
            ),
            Project(
                name="Курская_САУ_1",
                description="Система автоматического управления дизель-генератора",
                client="Курская",
                unit=1,
                type="САУ"
            ),
        ]
        
        for project in projects:
            db.add(project)
        
        db.commit()
        print(f"✅ Создано {len(projects)} тестовых проектов")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_projects()