#!/bin/sh

echo "Applying migrations..."

uv run alembic upgrade head

echo "Starting application..."

uv run fastapi run app/main.py --port 8000 --proxy-headers --forwarded-allow-ips="*" --root-path /api
