#!/usr/bin/env bash
python init_db.py     - скрипт для инициализации БД

python migrate_db.py     - скрипт для миграции БД

python seed_data.py

uv run uvicorn app.main:app --reload --port 3000
