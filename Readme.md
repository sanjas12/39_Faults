# Faults

## Требования
- [Visual C++ Redistributable 2015–2022](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- ОС: Windows 7 и выше

## Запуск


## Проблемы

TODO

# Рекомендация: замените init_db.py и migrate_db.py на Alembic (для обучения)
Так как вы учитесь, сейчас самое время освоить Alembic — это профессиональный инструмент для миграций (как Liquibase в Java).

Как перейти на Alembic (пошагово):

Установите Alembic (если еще нет):
uv pip install alembic

Инициализируйте Alembic в папке backend/:
alembic init -t async migrations
(Если используете синхронный SQLAlchemy, то просто alembic init migrations)

В файле alembic.ini поправьте строку:
sqlalchemy.url = sqlite:///./faults.db

В migrations/env.py укажите вашу Base (чтобы Alembic видел модели):
target_metadata = [Base.metadata] (импортируйте из app.models.all_models)

Создайте первую миграцию:
alembic revision --autogenerate -m "Initial tables"

Примените:
alembic upgrade head

Преимущество: Теперь структура БД будет меняться контролируемо, и вы сможете откатывать изменения.