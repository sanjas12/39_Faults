```markdown
# CONTEXT.md — Faults Backend

## Что это за проект

REST API-бэкенд для системы отслеживания неисправностей (fault tracking).
Принимает данные о неисправностях от клиентов (React/TypeScript фронтенд),
хранит их в реляционной БД и предоставляет CRUD-интерфейс.
Целевая среда — Windows 7+, Python 3.8.10, запуск как сервис или exe-сборка.
Язык интерфейса — русский (сообщения об ошибках, документация).

## Архитектура

```
React (порт 3000) ──HTTP──► FastAPI (порт 3000) ──SQLAlchemy──► SQLite / другая БД
```

| Слой | Модуль | Ответственность |
|------|--------|-----------------|
| API | `app/api/` | HTTP-эндпоинты, маршрутизация, валидация запросов |
| Схемы | `app/schemas/` | Pydantic-модели: входные/выходные DTO |
| Модели | `app/models/` | SQLAlchemy ORM-сущности, маппинг таблиц |
| Core | `app/core/` | Конфигурация, подключение к БД, безопасность |
| Сервисы | `app/services/` | Бизнес-логика (заглушки, в работе) |

**Точки входа:**
- `app/main.py` — FastAPI-приложение, CORS, регистрация роутеров
- `init_db.py` — разовый скрипт создания таблиц (`Base.metadata.create_all`)
- `build.py` — сборка в exe через cx_Freeze

**Ключевые зависимости:**

| Пакет | Зачем |
|-------|-------|
| `fastapi` | Web-фреймворк, авто-Swagger на `/docs` |
| `sqlalchemy` | ORM, поддержка нескольких СУБД |
| `pydantic-settings` | Конфигурация через `.env` / переменные окружения |
| `uvicorn` | ASGI-сервер |
| `uv` | Быстрый менеджер зависимостей и venv (внешний инструмент) |
| `cx_Freeze` | Сборка в Windows exe (только в `build.py`) |

## Структура файлов

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, подключение роутеров
│   ├── __init__.py
│   ├── api/
│   │   ├── faults.py        # CRUD для /faults — единственный рабочий роутер
│   │   ├── projects.py      # Заглушка (пусто)
│   │   ├── dashboard.py     # Заглушка (пусто)
│   │   └── knowledge_base.py# Заглушка (пусто)
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings), читает .env
│   │   ├── database.py      # engine, SessionLocal, Base, get_db()
│   │   └── security.py      # Заглушка (JWT не реализован)
│   ├── models/
│   │   ├── all_models.py    # Project + Fault — основные ORM-модели
│   │   └── project.py       # Дублирует Project из all_models (расхождение!)
│   └── schemas/
│       └── fault.py         # FaultBase / FaultCreate / FaultResponse
├── _version.py              # Версия + git-ревизия; импортируется в main.py
├── init_db.py               # Одноразовый скрипт инициализации БД
├── build.py                 # cx_Freeze сборка в exe
├── pyproject.toml           # Зависимости, настройки ruff/uv
├── requirements.txt         # Автогенерат uv export (не редактировать вручную)
├── uv.lock                  # Locked-граф зависимостей
├── faults.db                # SQLite база (gitignore в проде)
└── .python-version          # Фиксирует Python 3.8
```

## Соглашения

**Именование:**
- Классы: `PascalCase` (модели, схемы, Settings)
- Функции/переменные: `snake_case`
- Роутеры: именованный `router = APIRouter(prefix="/...", tags=[...])`
- Константы/команды git: `UPPER_SNAKE_CASE`

**Паттерны:**
- Dependency Injection через `Depends(get_db)` — сессия БД не создаётся вручную
- DTO-разделение: отдельные классы `Create` / `Response` на каждую сущность
- `model_dump()` при создании ORM-объекта из схемы (Pydantic v2)
- Конфигурация только через `Settings`; голые строки-константы в коде не используются
- Маркеры платформы (`sys_platform == 'win32'`) в зависимостях — проект собирается только под Windows

**Не делать:**
- Не редактировать `requirements.txt` вручную — он генерируется `uv export`
- Не создавать сессию БД напрямую — только через `get_db()`
- Не смешивать бизнес-логику в API-роутерах — она идёт в `app/services/`
- Не дублировать модели (см. известные проблемы ниже)

## Ключевые решения

**SQLite по умолчанию**
Выбран для простоты первоначального запуска (`faults.db` рядом с кодом).
`database_url` вынесен в `Settings`, поэтому замена на PostgreSQL —
только смена одной переменной окружения; `connect_args` уже обёрнут в условие.

**Python 3.8 + Windows-only зависимости**
Целевая машина — Windows 7 с Python 3.8.10.
`[tool.uv] environments` и маркеры `sys_platform == 'win32'` исключают
Linux/macOS из lock-файла намеренно. Раскомментировать linux-строку —
только при переносе сборки на Linux CI.

**`_version.py` с git-ревизией**
Версия строится из `__version__` + счётчика коммитов git.
При сборке в exe ревизия "запекается" в `_revision.py` (кладётся рядом
с бинарником), чтобы не зависеть от наличия git на машине пользователя.

**cx_Freeze вместо PyInstaller**
Выбран для совместимости с Windows 7 и Python 3.8.
`build.py` содержит список `REMOVE_DIRS` для ручной очистки мусора
(translations, sample_data и т.д.) — cx_Freeze не умеет исключать
подпапки пакетов из коробки.

## Текущий статус

**Реализовано:**
- CRUD для `Fault`: создание, список, получение по id (`app/api/faults.py`)
- ORM-модели `Fault` и `Project` (`app/models/all_models.py`)
- Конфигурация через `.env` / переменные окружения
- CORS для React dev-сервера (localhost:3000)
- Swagger UI на `/docs`
- Скрипт инициализации БД

**В работе / заглушки:**
- `app/api/projects.py` — пусто
- `app/api/dashboard.py` — пусто
- `app/api/knowledge_base.py` — пусто
- `app/core/security.py` — JWT не реализован
- `app/services/` — escalation, notifications, search — пусты

**Открытые вопросы / известные проблемы:**
- `app/models/all_models.py` и `app/models/project.py` оба определяют класс
  `Project` с одним `__tablename__ = "projects"` — SQLAlchemy выдаст ошибку
  при импорте обоих. Нужно удалить дубль или объединить.
- Роутеры из `app/api/` не подключены к `app/main.py` через `include_router` —
  необходимо добавить перед запуском.
- JWT (security.py) не реализован, но поле `secret_key` в Settings уже есть.
- Порт в `uvicorn.run` и `allow_origins` CORS указан `3000`, хотя стандартный
  порт FastAPI — `8000`; возможная коллизия с React dev-сервером.

## Глоссарий

| Термин | Значение |
|--------|----------|
| **Fault** | Неисправность — основная сущность системы |
| **Project** | Проект, к которому привязана неисправность |
| **severity** | Критичность: `critical` / `major` / `minor` |
| **status** | Статус неисправности: `open` / `in_progress` / `closed` |
| **uv** | Быстрый Python package manager от Astral (замена pip+venv) |
| **DTO** | Data Transfer Object — Pydantic-схема для входа/выхода API |
| **lock-файл** | `uv.lock` — воспроизводимый граф зависимостей |
| **запечённая ревизия** | `_revision.py`, создаваемый при сборке exe с номером коммита |
```
