FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home appuser \
    && mkdir -p /app/resources /app/logs \
    && chown appuser:appuser /app/resources /app/logs && chown appuser:appuser /app/resources

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev \
    && chown -R appuser:appuser /app/.venv

COPY --chown=appuser:appuser . .

RUN chmod +x /app/entrypoint.sh

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
