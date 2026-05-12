from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from api.errors import setup_exceptions
from api.middlewares import setup_middlewares
from api.routes import setup_routes
from core.config import settings
from core.database import db_helper
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    yield
    await db_helper.dispose()


app = FastAPI(
    lifespan=lifespan,
    title=settings.api_config.title,
    description=settings.api_config.description,
    version=settings.api_config.version,
)

setup_routes(app, prefix=settings.api_config.prefix)
setup_exceptions(app)
setup_middlewares(app)

if __name__ == "__main__":
    uvicorn.run(app, host=settings.run_config.host, port=settings.run_config.port)
