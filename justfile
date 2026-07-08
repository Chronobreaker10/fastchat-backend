set shell := ["powershell", "-c"]

@a_default:
    just --list

@run port="80":
    uv run fastapi run --port {{port}}

@lint:
    uv run ruff check --fix

@format:
    uv run ruff format

@test:
    uv run pytest

@docker-up:
    docker-compose up -d

@docker-down:
    docker-compose down

@migrate:
    docker exec promo_service uv run alembic upgrade head

@migrate-create message:
    docker exec promo_service uv run alembic revision --autogenerate -m "{{message}}"

# Откатить последнюю миграцию
@migrate-rollback:
    docker exec promo_service uv run alembic downgrade -1

# Показать историю миграций
@migrate-history:
    docker exec promo_service uv run alembic history

# Показать текущую версию
@migrate-current:
    docker exec promo_service uv run alembic current

# Создание окружения
@setup:
    if [ ! -d ".venv" ]; then uv venv; fi
    uv sync
