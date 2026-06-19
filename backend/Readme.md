# Title

✅ Дашборд — статистика и последние неисправности

✅ Проекты — управление проектами (CRUD)

✅ Неисправности — таблица с фильтрами и пагинацией

✅ Детальная страница — с комментариями и историей

✅ Kanban доска — визуальное управление задачами


## Запуск приложения (из репозитория)

### 1. Требования

| Параметр | Значение |
|---|---|
| Python | 3.8.10 |
| ОС | Windows 7 и выше |
| [uv](https://github.com/astral-sh/uv) | 0.11.7 |

### 2. Настройка окружения

#### 2.1 Создание виртуального окружения для backend (VSCode)

```bash
bash scripts/init_backend_env.sh
```

#### 2.2 Установка зависимостей (если скрипт из пункта 2.1 не сработал)

Рекомендуется — через [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

Без uv:

```bash
pip install -r requirements.txt
```

> `requirements.txt` генерируется из `pyproject.toml` — не редактировать вручную.

### 3. Запуск

#### 3.1 C uv

```bash
uv run python backend/init_db.py     - скрипт для инициализации БД

cd backend
uv run uvicorn app.main:app --reload --port 3000
http://localhost:3000/docs  -> Swagger UI
```

#### 3.2 Без uv

```bash
cd backend

source .venv/Scripts/activate

python init_db.py                                               - скрипт для инициализации БД

uvicorn app.main:app --reload --port 3000                       - для localhost
uvicorn app.main:app --reload --host 0.0.0.0 --port 3000        - для сети

python seed_data.py                                             - Наполняем тестовыми данными 

http://localhost:3000/docs                                      -> Swagger UI
```

---

## Запуск приложения (Windows — exe)

### Требования

- [Visual C++ Redistributable 2015–2022](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- ОС: Windows 7 и выше

## help

TODO
