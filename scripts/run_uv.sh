#!/usr/bin/env bash

uv run python init_db.py

uv run python migrate_db.py

uv run python seed_data.py

uv run uvicorn app.main:app --reload --port 3000
