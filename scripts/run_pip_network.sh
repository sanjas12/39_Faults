#!/usr/bin/env bash
export PYTHONIOENCODING=utf-8

rm faults.db

source .venv/Scripts/activate

python init_db.py

python migrate_db.py

python seed_data.py

uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
