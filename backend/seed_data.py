from app.core.database import SessionLocal
from app.models.all_models import Project, Fault
from datetime import datetime

def seed_data():
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже проекты
        if db.query(Project).count() > 0:
            print("📦 Данные уже есть в БД")
            return
        
        # Создаём проекты
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
        db.flush()  # Получаем ID проектов
        
        # Создаём неисправности для проектов
        faults = [
            Fault(
                title="Ошибка контроллера на ТЭЦ-5",
                description="PLC выдаёт ошибку 0xE4 при запуске котла №3",
                severity="critical",
                status="open",
                project_id=projects[0].id
            ),
            Fault(
                title="Сбой связи с датчиком давления",
                description="Потеря данных с датчика P-102 на магистрали",
                severity="major",
                status="in_progress",
                project_id=projects[1].id
            ),
            Fault(
                title="Некорректная калибровка робота",
                description="Робот на линии сборки отклоняется от траектории на 2мм",
                severity="minor",
                status="review",
                project_id=projects[2].id
            ),
            Fault(
                title="Зависание SCADA интерфейса",
                description="Система мониторинга перестаёт обновлять данные раз в 10 минут",
                severity="major",
                status="open",
                project_id=projects[1].id
            ),
            Fault(
                title="Перегрев блока питания контроллера",
                description="Температура блока питания достигает 85°C",
                severity="critical",
                status="open",
                project_id=projects[0].id
            ),
        ]
        
        for fault in faults:
            db.add(fault)
        
        db.commit()
        print(f"✅ Создано {len(projects)} проектов и {len(faults)} неисправностей")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()