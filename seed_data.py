from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.all_models import Fault, Project, User, UserRole, FaultComment, FaultHistory
from datetime import datetime, timedelta
import random

def seed_data():
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже пользователи
        if db.query(User).count() > 0:
            print("📦 Данные уже есть в БД")
            print("   Чтобы пересоздать данные, удалите файл faults.db и запустите скрипт заново.")
            return

        print("🚀 Начинаем наполнение базы данных...")

        # ===== СОЗДАЁМ ПОЛЬЗОВАТЕЛЕЙ =====
        users = [
            User(
                username="admin",
                email="admin@diakont.com",
                password_hash=get_password_hash("admin123"),
                full_name="Администратор Системы",
                role=UserRole.ADMIN,
                is_active=True,
            ),
            User(
                username="engineer",
                email="engineer@diakont.com",
                password_hash=get_password_hash("eng123"),
                full_name="Иванов Иван Петрович",
                role=UserRole.ENGINEER,
                is_active=True,
            ),
            User(
                username="engineer2",
                email="engineer2@diakont.com",
                password_hash=get_password_hash("eng123"),
                full_name="Петров Пётр Сергеевич",
                role=UserRole.ENGINEER,
                is_active=True,
            ),
            User(
                username="manager",
                email="manager@diakont.com",
                password_hash=get_password_hash("ma123"),
                full_name="Сидорова Мария Ивановна",
                role=UserRole.MANAGER,
                is_active=True,
            ),
            User(
                username="operator",
                email="operator@diakont.com",
                password_hash=get_password_hash("op123"),
                full_name="Козлов Дмитрий Алексеевич",
                role=UserRole.MANAGER,
                is_active=True,
            ),
        ]

        for user in users:
            db.add(user)
        db.flush()
        print(f"   ✅ Создано {len(users)} пользователей")

        # ===== СОЗДАЁМ ПРОЕКТЫ =====
        projects_data = [
            {
                "name": "Кольская САРЗ-1",
                "description": "Модернизация системы управления котлами ТЭЦ-5",
                "client": "Кольская АЭС",
                "unit": 1,
                "type": "САРЗ",
            },
            {
                "name": "Кольская САРЗ-2",
                "description": "Внедрение системы диспетчерского контроля нефтепровода",
                "client": "Кольская АЭС",
                "unit": 2,
                "type": "САРЗ",
            },
            {
                "name": "Смоленская САРЗ-2",
                "description": "Система автоматического управления дизель-генератора",
                "client": "Смоленская АЭС",
                "unit": 2,
                "type": "САРЗ",
            },
            {
                "name": "Курская САУ-1",
                "description": "Система автоматического управления турбиной К-500",
                "client": "Курская АЭС",
                "unit": 1,
                "type": "САУ",
            },
            {
                "name": "Ленинградская САУ-3",
                "description": "Автоматизация системы охлаждения реактора",
                "client": "Ленинградская АЭС",
                "unit": 3,
                "type": "САУ",
            },
            {
                "name": "Нововоронежская САРЗ-1",
                "description": "Резервирование системы управления парогенераторами",
                "client": "Нововоронежская АЭС",
                "unit": 1,
                "type": "САРЗ",
            },
        ]

        projects = []
        for p_data in projects_data:
            project = Project(**p_data)
            db.add(project)
            projects.append(project)
        db.flush()
        print(f"   ✅ Создано {len(projects)} проектов")

        # ===== СОЗДАЁМ НЕИСПРАВНОСТИ =====
        fault_templates = [
            {
                "title": "Ошибка контроллера {project_name}",
                "description": "PLC выдаёт ошибку 0xE{code} при запуске {component}",
                "severity": "critical",
                "status": "open",
            },
            {
                "title": "Сбой связи с датчиком {component}",
                "description": "Потеря данных с датчика {component} на {location}",
                "severity": "major",
                "status": "in_progress",
            },
            {
                "title": "Некорректная калибровка {component}",
                "description": "{component} на линии {line} отклоняется от нормы на {value}%",
                "severity": "minor",
                "status": "review",
            },
            {
                "title": "Зависание SCADA интерфейса",
                "description": "Система мониторинга перестаёт обновлять данные каждые {time} минут",
                "severity": "major",
                "status": "open",
            },
            {
                "title": "Перегрев блока питания контроллера",
                "description": "Температура блока питания достигает {temp}°C",
                "severity": "critical",
                "status": "closed",
            },
            {
                "title": "Аварийное отключение {component}",
                "description": "Произошло автоматическое отключение {component} по причине {reason}",
                "severity": "critical",
                "status": "open",
            },
            {
                "title": "Некорректные показания датчика {component}",
                "description": "Показания датчика {component} отличаются от эталонных на {value}%",
                "severity": "major",
                "status": "in_progress",
            },
            {
                "title": "Сбой в системе резервирования",
                "description": "При переключении на резервный канал произошла ошибка {error_code}",
                "severity": "critical",
                "status": "review",
            },
        ]

        components = ["температуры", "давления", "уровня", "положения", "вибрации", "тока", "напряжения"]
        locations = ["на магистрали", "в турбинном цехе", "на трубопроводе", "в распределительном щите"]
        
        faults = []
        statuses = ["open", "in_progress", "review", "closed"]
        severities = ["critical", "major", "minor", "trivial"]
        
        # Генерируем неисправности для каждого проекта
        for i, project in enumerate(projects):
            # Для каждого проекта создаём от 3 до 7 неисправностей
            num_faults = random.randint(3, 7)
            
            for j in range(num_faults):
                template = random.choice(fault_templates)
                component = random.choice(components)
                
                # Заменяем плейсхолдеры
                title = template["title"].format(
                    project_name=project.name,
                    component=component,
                )
                
                description = template["description"].format(
                    project_name=project.name,
                    component=component,
                    code=random.randint(1, 9),
                    location=random.choice(locations),
                    line=random.randint(1, 5),
                    value=random.randint(5, 30),
                    time=random.randint(5, 15),
                    temp=random.randint(75, 95),
                    reason=random.choice(["перегрузка", "короткое замыкание", "обрыв цепи", "сбой ПО"]),
                    error_code=random.randint(100, 999),
                )
                
                # Выбираем статус и важность
                if j < 2:  # Первые 2 неисправности в проекте — открытые
                    status = "open"
                    severity = random.choice(["critical", "major"])
                elif j < 4:
                    status = random.choice(["in_progress", "review"])
                    severity = random.choice(["major", "minor"])
                else:
                    status = random.choice(["review", "closed"])
                    severity = random.choice(["minor", "trivial"])
                
                # Для разнообразия, иногда меняем
                if random.random() > 0.7:
                    status = random.choice(statuses)
                    severity = random.choice(severities)
                
                fault = Fault(
                    title=title[:200],
                    description=description[:500],
                    severity=severity,
                    status=status,
                    project_id=project.id,
                )
                db.add(fault)
                faults.append(fault)
                
        db.flush()
        print(f"   ✅ Создано {len(faults)} неисправностей")

        # ===== СОЗДАЁМ ИСТОРИЮ ДЛЯ НЕИСПРАВНОСТЕЙ =====
        print("   📝 Создаём историю для неисправностей...")
        
        history_authors = ["admin", "engineer", "engineer2", "manager", "operator"]
        status_labels = {
            "open": "Открыта",
            "in_progress": "В работе",
            "review": "На проверке",
            "closed": "Закрыта"
        }
        severity_labels = {
            "critical": "Критическая",
            "major": "Серьёзная",
            "minor": "Незначительная",
            "trivial": "Тривиальная"
        }
        
        for fault in faults:
            # 1. Создание неисправности
            author = random.choice(history_authors)
            created_date = fault.created_at - timedelta(days=random.randint(0, 3))
            
            creation_history = FaultHistory(
                fault_id=fault.id,
                event_type="creation",
                field="creation",
                old_value=None,
                new_value=f"Создана неисправность: {fault.title}",
                author=author,
                created_at=created_date
            )
            db.add(creation_history)
            
            # 2. Если статус изменился — добавляем историю изменений статуса
            if fault.status != "open" and random.random() > 0.3:
                status_change_date = created_date + timedelta(hours=random.randint(1, 24))
                new_status = fault.status
                old_status = "open"
                
                if new_status == "in_progress":
                    old_status = "open"
                elif new_status == "review":
                    old_status = random.choice(["open", "in_progress"])
                elif new_status == "closed":
                    old_status = random.choice(["open", "in_progress", "review"])
                
                status_history = FaultHistory(
                    fault_id=fault.id,
                    event_type="field_change",
                    field="Статус",
                    old_value=status_labels.get(old_status, old_status),
                    new_value=status_labels.get(new_status, new_status),
                    author=random.choice(history_authors),
                    created_at=status_change_date
                )
                db.add(status_history)
            
            # 3. Если важность изменилась — добавляем историю
            if fault.severity != "minor" and random.random() > 0.5:
                severity_change_date = created_date + timedelta(hours=random.randint(2, 48))
                old_severity = random.choice(["minor", "major"])
                new_severity = fault.severity
                
                if new_severity == "critical":
                    old_severity = random.choice(["major", "minor"])
                elif new_severity == "major":
                    old_severity = random.choice(["minor", "trivial"])
                
                severity_history = FaultHistory(
                    fault_id=fault.id,
                    event_type="field_change",
                    field="Важность",
                    old_value=severity_labels.get(old_severity, old_severity),
                    new_value=severity_labels.get(new_severity, new_severity),
                    author=random.choice(history_authors),
                    created_at=severity_change_date
                )
                db.add(severity_history)

        print(f"   ✅ Создана история для неисправностей")

        # ===== СОЗДАЁМ КОММЕНТАРИИ =====
        print("   💬 Создаём комментарии...")
        
        comment_authors = ["engineer", "engineer2", "manager", "operator"]
        comment_texts = [
            "Проверил, подтверждаю проблему.",
            "Начал диагностику, предварительно проблема в блоке питания.",
            "Заменил датчик, наблюдаю за показаниями.",
            "Требуется замена модуля, заказал запчасти.",
            "Проблема устранена, провел тестирование.",
            "Временное решение внедрено, ждем замену.",
            "Не удается воспроизвести ошибку, нужны дополнительные логи.",
            "Связался с поставщиком, жду ответа.",
            "Обновил ПО, ошибка исчезла.",
            "Провел дополнительное тестирование, всё работает штатно.",
        ]
        
        for fault in faults:
            # Для каждой неисправности создаём от 0 до 3 комментариев
            num_comments = random.randint(0, 3)
            for _ in range(num_comments):
                comment = FaultComment(
                    fault_id=fault.id,
                    author=random.choice(comment_authors),
                    content=random.choice(comment_texts),
                    is_internal=1 if random.random() > 0.7 else 0,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 10)),
                )
                db.add(comment)
                
        print(f"   ✅ Созданы комментарии к неисправностям")

        db.commit()

        # ===== ВЫВОД СТАТИСТИКИ =====
        print("\n" + "="*50)
        print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
        print("="*50)
        
        total_users = db.query(User).count()
        total_projects = db.query(Project).count()
        total_faults = db.query(Fault).count()
        total_comments = db.query(FaultComment).count()
        total_history = db.query(FaultHistory).count()
        
        print(f"   👤 Пользователей: {total_users}")
        print(f"   📁 Проектов: {total_projects}")
        print(f"   🐛 Неисправностей: {total_faults}")
        print(f"   💬 Комментариев: {total_comments}")
        print(f"   📜 Записей истории: {total_history}")
        
        print("\n   📊 Статусы неисправностей:")
        for status in ["open", "in_progress", "review", "closed"]:
            count = db.query(Fault).filter(Fault.status == status).count()
            print(f"      {status}: {count}")
        
        print("\n   📊 Важность неисправностей:")
        for severity in ["critical", "major", "minor", "trivial"]:
            count = db.query(Fault).filter(Fault.severity == severity).count()
            print(f"      {severity}: {count}")
        
        print("\n" + "="*50)
        print("🔑 ДАННЫЕ ДЛЯ ВХОДА:")
        print("   👤 admin / admin123 (Администратор)")
        print("   👤 engineer / eng123 (Инженер)")
        print("   👤 engineer2 / eng123 (Инженер)")
        print("   👤 manager / ma123 (Менеджер)")
        print("   👤 operator / op123 (Оператор)")
        print("="*50)
        print("✅ Готово! Запустите сервер и откройте http://localhost:3000")
        print("   Не забудьте выполнить миграции БД: python init_db.py")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()