from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.all_models import (
    Fault, Project, User, UserRole, FaultComment, 
    FaultHistory, KnowledgeBase, FaultAttachment
)
from datetime import datetime, timedelta
import random
import os
from pathlib import Path

# ===== КОНТАКТНЫЕ ДАННЫЕ ДЛЯ ПРОЕКТОВ =====
CONTACTS = [
    {
        "name": "Иванов Иван Иванович",
        "phone": "+7 (495) 123-45-67",
        "email": "i.ivanov@kolskaya.ru",
        "position": "Главный инженер проекта"
    },
    {
        "name": "Петров Пётр Петрович",
        "phone": "+7 (495) 234-56-78",
        "email": "p.petrov@kolskaya.ru",
        "position": "Ведущий инженер"
    },
    {
        "name": "Сидорова Мария Ивановна",
        "phone": "+7 (495) 345-67-89",
        "email": "m.sidorova@smolensk.ru",
        "position": "Руководитель проекта"
    },
    {
        "name": "Козлов Дмитрий Алексеевич",
        "phone": "+7 (495) 456-78-90",
        "email": "d.kozlov@kursk.ru",
        "position": "Инженер-электроник"
    },
    {
        "name": "Смирнов Андрей Васильевич",
        "phone": "+7 (495) 567-89-01",
        "email": "a.smirnov@leningrad.ru",
        "position": "Главный специалист"
    },
    {
        "name": "Волкова Екатерина Дмитриевна",
        "phone": "+7 (495) 678-90-12",
        "email": "e.volkova@novovoronezh.ru",
        "position": "Инженер-программист"
    },
    {
        "name": "Новиков Сергей Олегович",
        "phone": "+7 (495) 789-01-23",
        "email": "s.novikov@balakovo.ru",
        "position": "Технический директор"
    },
    {
        "name": "Морозова Анна Сергеевна",
        "phone": "+7 (495) 890-12-34",
        "email": "a.morozova@rostov.ru",
        "position": "Ведущий инженер-электроник"
    },
]

# ===== РАСШИРЕННЫЙ СПИСОК СТАНЦИЙ =====
STATIONS = [
    "Кольская", "Смоленская", "Курская", "Ленинградская", 
    "Нововоронежская", "Балаковская", "Ростовская", "Калининская",
    "Тверская", "Ярославская", "Владимирская", "Нижегородская",
    "Казанская", "Самарская", "Саратовская", "Волгоградская"
]

# ===== РАСШИРЕННЫЙ СПИСОК ТИПОВ =====
TYPES = ["САРЗ", "САУ", "САР", "САУ-Т", "САРЗ-М", "САУ-К", "САР-Н"]

# ===== РАСШИРЕННЫЙ СПИСОК КЛИЕНТОВ =====
CLIENTS = [
    "Росатом", "Росэнергоатом", "ТГК-1", "ТГК-2", "ТГК-3",
    "Мосэнерго", "Ленэнерго", "Кубаньэнерго", "Смоленскэнерго",
    "Курскэнерго", "Балаковская АЭС", "Ростовская АЭС"
]

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
            # ✅ Добавляем дополнительных пользователей
            User(
                username="engineer3",
                email="engineer3@diakont.com",
                password_hash=get_password_hash("eng123"),
                full_name="Смирнов Андрей Васильевич",
                role=UserRole.ENGINEER,
                is_active=True,
            ),
            User(
                username="engineer4",
                email="engineer4@diakont.com",
                password_hash=get_password_hash("eng123"),
                full_name="Волкова Екатерина Дмитриевна",
                role=UserRole.ENGINEER,
                is_active=True,
            ),
            User(
                username="operator2",
                email="operator2@diakont.com",
                password_hash=get_password_hash("op123"),
                full_name="Новиков Сергей Олегович",
                role=UserRole.MANAGER,
                is_active=True,
            ),
        ]

        for user in users:
            db.add(user)
        db.flush()
        print(f"   ✅ Создано {len(users)} пользователей")

        # ===== СОЗДАЁМ ПРОЕКТЫ (УВЕЛИЧЕНО ДО 24) =====
        projects_data = []
        
        # Генерируем 24 проекта (3x от 8)
        for i in range(24):
            station = random.choice(STATIONS)
            type_ = random.choice(TYPES)
            unit = random.randint(1, 4)
            client = random.choice(CLIENTS)
            
            projects_data.append({
                "name": f"{station} {type_}-{unit}",
                "description": f"Проект автоматизации на {station} (блок {unit}, тип {type_})",
                "client": client,
                "station": station,
                "unit": unit,
                "type": type_,
            })

        projects = []
        for i, p_data in enumerate(projects_data):
            contact = CONTACTS[i % len(CONTACTS)]
            project = Project(
                name=p_data["name"],
                description=p_data["description"],
                client=p_data["client"],
                station=p_data["station"],
                unit=p_data["unit"],
                type=p_data["type"],
                contact_name=contact["name"],
                contact_phone=contact["phone"],
                contact_email=contact["email"],
                contact_position=contact["position"],
            )
            db.add(project)
            projects.append(project)
        db.flush()
        print(f"   ✅ Создано {len(projects)} проектов с контактной информацией")

        # ===== СОЗДАЁМ НЕИСПРАВНОСТИ (УВЕЛИЧЕНО В 3 РАЗА) =====
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
            {
                "title": "Пропадание питания на {component}",
                "description": "На {component} пропало питание на {time} секунд",
                "severity": "major",
                "status": "open",
            },
            {
                "title": "Ошибка синхронизации данных",
                "description": "Расхождение данных между основным и резервным сервером на {value}%",
                "severity": "minor",
                "status": "in_progress",
            },
        ]

        # Шаблоны для планируемых мероприятий
        planned_actions_templates = [
            """# План мероприятий

## Немедленные действия
- **Отключить проблемный модуль**
- Проверить журналы ошибок
- Связаться с поставщиком

## Диагностика
1. Проверить целостность кабелей
2. Измерить напряжение на входах
3. Протестировать резервный канал

## Устранение
- Заменить неисправный компонент
- Обновить прошивку
- Провести калибровку

## Контроль
- Проверить работу после замены
- Задокументировать решение""",
            
            """# Мероприятия по устранению

## Этап 1: Подготовка
- Согласовать план работ
- Подготовить необходимые инструменты
- Создать резервную копию конфигурации

## Этап 2: Выполнение
1. Остановить процесс
2. Выполнить замену оборудования
3. Проверить подключения

## Этап 3: Тестирование
- Провести функциональное тестирование
- Проверить все режимы работы
- Убедиться в отсутствии ошибок""",
            
            """# План восстановления

## Критические шаги
1. **Обесточить оборудование**
2. Проверить состояние компонентов
3. Заменить повреждённые элементы

## Дополнительные меры
- Обновить документацию
- Провести инструктаж персонала
- Установить мониторинг

## Контрольные точки
- [x] Проверка питания
- [ ] Проверка сигналов
- [ ] Проверка связи с SCADA""",
            
            """# Программа работ

## Основные задачи
- **Диагностика системы**
- **Выявление корневой причины**
- **Устранение неисправности**
- **Валидация решения**

## Ответственные
- Инженер-электроник
- Инженер-программист
- Руководитель

## Сроки
- Начало: {date}
- Окончание: {date}

## Ресурсы
- Измерительное оборудование
- Запасные компоненты
- Техническая документация""",
        ]

        CATEGORIES = [
            "Аппаратная неисправность",
            "Программная ошибка",
            "Сбой связи",
            "Ошибка пользователя",
            "Профилактика",
            "Модернизация",
            "Другое",
            "Документация",
            "Алгоритм"
        ]

        components = ["температуры", "давления", "уровня", "положения", "вибрации", "тока", "напряжения", "частоты", "фазы"]
        locations = ["на магистрали", "в турбинном цехе", "на трубопроводе", "в распределительном щите", "на пульте управления", "в серверной"]
        
        faults = []
        
        # Генерируем неисправности для каждого проекта (увеличено до 9-15 на проект)
        for i, project in enumerate(projects):
            num_faults = random.randint(9, 15)  # Было 3-7
            
            for j in range(num_faults):
                template = random.choice(fault_templates)
                component = random.choice(components)
                
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
                    reason=random.choice(["перегрузка", "короткое замыкание", "обрыв цепи", "сбой ПО", "износ оборудования"]),
                    error_code=random.randint(100, 999),
                )
                
                # Распределение статусов
                if j < 3:
                    status = "open"
                    severity = random.choice(["critical", "major"])
                elif j < 6:
                    status = random.choice(["in_progress", "review"])
                    severity = random.choice(["major", "minor"])
                elif j < 9:
                    status = random.choice(["review", "closed"])
                    severity = random.choice(["minor", "trivial"])
                else:
                    status = random.choice(["open", "in_progress", "review", "closed"])
                    severity = random.choice(["critical", "major", "minor", "trivial"])
                
                category = random.choice(CATEGORIES) if random.random() > 0.15 else None
                
                planned_actions = None
                if random.random() > 0.35:
                    action_template = random.choice(planned_actions_templates)
                    if "{date}" in action_template:
                        date = (datetime.now() + timedelta(days=random.randint(1, 14))).strftime("%d.%m.%Y")
                        planned_actions = action_template.format(date=date)
                    else:
                        planned_actions = action_template
                
                fault = Fault(
                    title=title[:200],
                    description=description[:500],
                    severity=severity,
                    status=status,
                    category=category,
                    project_id=project.id,
                    planned_actions=planned_actions,
                )
                db.add(fault)
                faults.append(fault)
                
        db.flush()
        print(f"   ✅ Создано {len(faults)} неисправностей")

        # ===== СОЗДАЁМ ИСТОРИЮ ДЛЯ НЕИСПРАВНОСТЕЙ =====
        print("   📝 Создаём историю для неисправностей...")
        
        history_authors = ["admin", "engineer", "engineer2", "manager", "operator", "engineer3", "engineer4", "operator2"]
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
            author = random.choice(history_authors)
            created_date = fault.created_at - timedelta(days=random.randint(0, 5))
            
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
            
            # Добавляем несколько изменений статуса
            num_changes = random.randint(0, 3)
            current_status = "open"
            for _ in range(num_changes):
                new_status = random.choice(["in_progress", "review", "closed"])
                if new_status != current_status:
                    status_change_date = created_date + timedelta(hours=random.randint(1, 48))
                    status_history = FaultHistory(
                        fault_id=fault.id,
                        event_type="field_change",
                        field="Статус",
                        old_value=status_labels.get(current_status, current_status),
                        new_value=status_labels.get(new_status, new_status),
                        author=random.choice(history_authors),
                        created_at=status_change_date
                    )
                    db.add(status_history)
                    current_status = new_status
            
            # Добавляем изменение важности
            if random.random() > 0.5:
                severity_change_date = created_date + timedelta(hours=random.randint(2, 48))
                old_severity = random.choice(["minor", "major"])
                new_severity = fault.severity
                if old_severity != new_severity:
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

        # ===== СОЗДАЁМ КОММЕНТАРИИ (УВЕЛИЧЕНО) =====
        print("   💬 Создаём комментарии...")
        
        comment_authors = ["engineer", "engineer2", "manager", "operator", "engineer3", "engineer4", "operator2"]
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
            "Требуется согласование с руководством.",
            "Запросил техническую документацию.",
            "Провел анализ логов, проблема в прошивке.",
            "Отправил запрос на замену оборудования.",
            "Провел профилактические работы.",
        ]
        
        for fault in faults:
            num_comments = random.randint(0, 5)  # Увеличено до 5
            for _ in range(num_comments):
                comment = FaultComment(
                    fault_id=fault.id,
                    author=random.choice(comment_authors),
                    content=random.choice(comment_texts),
                    is_internal=1 if random.random() > 0.7 else 0,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 14)),
                )
                db.add(comment)
                
        print(f"   ✅ Созданы комментарии к неисправностям")

        # ===== СОЗДАЁМ СТАТЬИ ДЛЯ БАЗЫ ЗНАНИЙ (УВЕЛИЧЕНО) =====
        print("   📚 Создаём статьи для базы знаний...")

        knowledge_articles = [
            {
                "title": "Как устранить ошибку PLC 0xE4",
                "content": """# Ошибка PLC 0xE4

## Причина
Ошибка возникает при перегреве блока питания контроллера.

## Решение
1. Отключите питание
2. Проверьте вентиляцию
3. Замените термопасту
4. Включите питание

## Профилактика
Проводите чистку каждые 3 месяцев.""",
                "category": "Решение",
                "tags": "plc, ошибка, контроллер",
                "author": "admin"
            },
            {
                "title": "Настройка SCADA для нефтепровода",
                "content": """# Настройка SCADA

## Шаг 1: Установка
Скачайте дистрибутив с сайта производителя.

## Шаг 2: Конфигурация
Откройте файл `config.ini` и настройте параметры.

## Шаг 3: Подключение
Настройте подключение к контроллерам.""",
                "category": "Инструкция",
                "tags": "scada, настройка, нефтепровод",
                "author": "engineer"
            },
            {
                "title": "Диагностика датчика давления",
                "content": """# Диагностика датчика давления

## Симптомы
- Нестабильные показания
- Потеря связи

## Проверка
1. Проверьте питание
2. Проверьте кабель
3. Проверьте калибровку

## Замена
При неисправности замените датчик.""",
                "category": "Документация",
                "tags": "датчик, давление, диагностика",
                "author": "engineer2"
            },
            {
                "title": "Аварийное отключение оборудования",
                "content": """# Аварийное отключение

## Алгоритм действий
1. **Немедленно** нажмите кнопку "СТОП"
2. Перекройте подачу рабочей среды
3. Обесточьте оборудование

## Действия после отключения
- Сообщите руководителю
- Зафиксируйте время отключения
- Начните диагностику

## Запрещено
- Включать оборудование без диагностики
- Самостоятельно устранять неисправности""",
                "category": "Инструкция",
                "tags": "авария, отключение, безопасность",
                "author": "admin"
            },
            {
                "title": "Калибровка датчиков температуры",
                "content": """# Калибровка датчиков температуры

## Подготовка
1. Отключите датчик от системы
2. Подготовьте эталонный термометр

## Калибровка
1. Поместите датчик в калибровочную среду
2. Сравните показания
3. Отрегулируйте при необходимости

## Проверка
- Проведите тестирование в рабочем режиме""",
                "category": "Инструкция",
                "tags": "калибровка, температура, датчик",
                "author": "engineer3"
            },
            {
                "title": "Обновление прошивки контроллера",
                "content": """# Обновление прошивки

## Подготовка
- Скачайте актуальную прошивку
- Сделайте резервную копию

## Процесс обновления
1. Подключитесь к контроллеру
2. Загрузите прошивку
3. Перезагрузите контроллер

## Проверка
- Проверьте версию прошивки
- Проверьте работоспособность""",
                "category": "Инструкция",
                "tags": "прошивка, обновление, контроллер",
                "author": "engineer4"
            },
        ]

        for article_data in knowledge_articles:
            article = KnowledgeBase(
                title=article_data["title"],
                content=article_data["content"],
                category=article_data["category"],
                tags=article_data["tags"],
                author=article_data["author"],
                is_published=True
            )
            db.add(article)

        print(f"   ✅ Созданы статьи для базы знаний")

        # ===== СОЗДАЁМ СВЯЗИ МЕЖДУ СТАТЬЯМИ И НЕИСПРАВНОСТЯМИ =====
        print("   🔗 Создаём связи между статьями и неисправностями...")

        all_articles = db.query(KnowledgeBase).all()
        all_faults = db.query(Fault).all()

        if all_articles and all_faults:
            for article in all_articles:
                num_faults = random.randint(2, 5)  # Увеличено до 5
                selected_faults = random.sample(all_faults, min(num_faults, len(all_faults)))
                fault_ids = [f.id for f in selected_faults]
                article.related_faults = ','.join([str(id) for id in fault_ids])
                db.add(article)
                
                for fault in selected_faults:
                    existing_ids = [int(id.strip()) for id in fault.linked_knowledge_ids.split(',') if id.strip()] if fault.linked_knowledge_ids else []
                    if article.id not in existing_ids:
                        existing_ids.append(article.id)
                        fault.linked_knowledge_ids = ','.join([str(id) for id in existing_ids])
                        db.add(fault)
            
            db.commit()
            print(f"   ✅ Созданы связи между статьями и неисправностями")

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
        total_knowledge = db.query(KnowledgeBase).count()
        
        faults_with_actions = db.query(Fault).filter(Fault.planned_actions.isnot(None)).count()
        
        print(f"   👤 Пользователей: {total_users}")
        print(f"   📁 Проектов: {total_projects}")
        print(f"   🐛 Неисправностей: {total_faults}")
        print(f"   📋 С планируемыми мероприятиями: {faults_with_actions}")
        print(f"   💬 Комментариев: {total_comments}")
        print(f"   📜 Записей истории: {total_history}")
        print(f"   📚 Статей в базе знаний: {total_knowledge}")
        
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
        print("   👤 engineer3 / eng123 (Инженер)")
        print("   👤 engineer4 / eng123 (Инженер)")
        print("   👤 manager / ma123 (Менеджер)")
        print("   👤 operator / op123 (Оператор)")
        print("   👤 operator2 / op123 (Оператор)")
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