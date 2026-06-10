я хочу написать приложение которое будет похожа на CRM и jira, но будет завязано на отслеживание неисправностей + база знаний про неиспраностям и проектам в которых они возникают. Неисправности возникают при эксплуатации разных систем автоматического управления (проекты). Неисправности должны добавляться вручную, редактироваться и т.д. Создай актуальный стэк технологии (python 3.8.10 + uv). это должно работать в браузере. мне нужна дорожная карта и это будет мой пет проект, в котором я буду учиться. я прикрепил примерную UX структуру:  дашборд с (неисправности + база знаний+ проекты). Kanban доска (по статусам Fault) — через react-beautiful-dnd Комментарии + история (как лента в Jira) Фильтры (по системе, severity, назначенному) Автоэскалация (Celery: каждые 10 мин проверяет sla_deadline и поднимает severity)/ подбери правильную архитектуру

Примерный стек-технологий, если надо критикуй или подбери актуальное

Актуальный стек (Python first, браузер)
Слой	Технология	Почему
Бэкенд	        FastAPI (асинхронный)	            Быстрый, автодока, WebSocket из коробки
ORM	            SQLAlchemy 2.0 (async) + Alembic	Работа с БД, миграции
База	        PostgreSQL	                        Надёжно, круто для аналитики (количество отказов по системам)
Авторизация 	JWT, python-jose                    Для JWT сессий и брокера задач
Фон. задачи	    BackgroundTasks (FastAPI)           Уведомления, неисправности → перейти на Celery позже
Фронтенд	    React + TypeScript + TanStack Query	Лучшее для таблиц/дашбордов + удобная работа с API
UI Компоненты	MUI (Material UI)	                Готовые таблицы, карточки, календарь (как на скрине)
Стейт-менеджментZustand (легче Redux)	        Для фильтров и текущего пользователя
Даты/время	    date-fns	                        Для “просрочено”, “сегодня”, “по приоритету”
Контейнеры	    Docker + docker-compose	            Поднимаете всё одной командой

Примерная структура проекта

39_Faults
 ┣ backend
 ┃ ┣ app
 ┃ ┃ ┣ api
 ┃ ┃ ┃ ┣ dashboard.py
 ┃ ┃ ┃ ┣ faults.py
 ┃ ┃ ┃ ┣ knowledge_base.py
 ┃ ┃ ┃ ┣ projects.py
 ┃ ┃ ┃ ┗ __init__.py
 ┃ ┃ ┣ core
 ┃ ┃ ┃ ┣ config.py
 ┃ ┃ ┃ ┣ database.py
 ┃ ┃ ┃ ┣ security.py
 ┃ ┃ ┃ ┗ __init__.py
 ┃ ┃ ┣ models
 ┃ ┃ ┃ ┣ project.py
 ┃ ┃ ┃ ┗ __init__.py
 ┃ ┃ ┣ schemas
 ┃ ┃ ┃ ┗ __init__.py
 ┃ ┃ ┗ services
 ┃ ┃ ┃ ┣ escalation.py
 ┃ ┃ ┃ ┣ notifications.py
 ┃ ┃ ┃ ┣ search.py
 ┃ ┃ ┃ ┗ __init__.py
 ┃ ┣ .python-version
 ┃ ┣ build.py
 ┃ ┣ main.py
 ┃ ┣ pyproject.toml
 ┃ ┣ requirements.txt
 ┃ ┗ _version.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FaultTable.tsx
│   │   │   ├── CommentThread.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   └── MarkdownEditor.tsx
│   │   ├── pages/     (Dashboard, FaultList, FaultDetail)
│   │   │   ├── Dashboard.tsx
│   │   │   ├── FaultList.tsx
│   │   │   ├── FaultDetail.tsx (с лентой комментариев)
│   │   │   ├── KanbanBoard.tsx
│   │   │   └── KnowledgeBase.tsx
│   │   └── api/
│   │   ├── hooks/
│   │   ├── api/ (React Query)
│   │   └── App.tsx
│   └── Dockerfile
 ┣ bugs
 ┃ ┗ bug-001.md
 ┣ docs
 ┃ ┣ Promt.md
 ┃ ┣ Readme.md
 ┃ ┗ RelNote.txt
 ┣ scripts
 ┃ ┣ run.sh
 ┃ ┣ toexe.sh
 ┃ ┗ venv_pip.sh
 ┣ .gitattributes
 ┣ .gitignore
 ┣ .pre-commit-config.yaml
 ┣ Readme.md
 ┗ structure
