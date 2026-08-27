#!/bin/sh
set -eu
alembic upgrade head
if [ "${DEMO_MODE:-false}" = "true" ]; then
	python scripts/seed_database.py
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
