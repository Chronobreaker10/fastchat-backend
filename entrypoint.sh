#!/bin/sh

echo "Applying migrations..."

uv run alembic upgrade head

echo "Starting application..."

uv run fastapi run main.py --port 8000