from app.core.database import SessionLocal
from app.models.all_models import Project, Fault, User, UserRole
from app.core.security import get_password_hash


def seed_data():
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже пользователи
        if db.query(User).count() > 0:
            print("📦 Данные уже есть в БД")
            return
        
        # ===== СОЗДАЁМ ПОЛЬЗОВАТЕЛЕЙ =====
        users = [
            User(
                username="admin",
                email="admin@diakont.com",
                password_hash=get_password_hash("admin123"),
                full_name="Администратор",
                role=UserRole.ADMIN,
                is_active=True
            ),
            User(
                username="engineer",
                email="engineer@diakont.com",
                password_hash=get_password_hash("eng123"),
                full_name="Инженер Иванов",
                role=UserRole.ENGINEER,
                is_active=True
            ),
            User(
                username="manager",
                email="manager@diakont.com",
                password_hash=get_password_hash("ma123"),
                full_name="Manager Петров",
                role=UserRole.MANAGER,
                is_active=True
            ),
        ]
        
        for user in users:
            db.add(user)
        db.flush()
        
        # ===== СОЗДАЁМ ПРОЕКТЫ (с полями unit и type) =====
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
        
        # ===== СОЗДАЁМ НЕИСПРАВНОСТИ =====
        faults = [
            Fault(
                title="Ошибка контроллера на Кольская_САРЗ_1",
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
                status="closed",
                project_id=projects[0].id
            ),
        ]
        
        for fault in faults:
            db.add(fault)
        
        db.commit()
        
        print(f"✅ Создано:")
        print(f"   👤 {len(users)} пользователей")
        print(f"   📁 {len(projects)} проектов")
        print(f"   🐛 {len(faults)} неисправностей")
        print()
        print("   🔑 Данные для входа:")
        print("      👤 admin / admin123 (Администратор)")
        print("      👤 engineer / eng123 (Инженер)")
        print("      👤 manager / ma123 (Менеджер)")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()