#!/bin/sh

echo "Applying migrations..."

uv run alembic upgrade head

echo "Starting application..."

uv run fastapi run app/main.py --port 8000 --host 0.0.0.0
