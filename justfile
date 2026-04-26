set shell := ["powershell", "-c"]

@a_default:
    just --list

@run:
    uv run fastapi run

@lint:
    uv run ruff check --fix

@format:
    uv run ruff format

@test:
    uv run pytest

@docker:
    docker compose up -d
