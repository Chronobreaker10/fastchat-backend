from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from api.errors import setup_exceptions
from api.middlewares import setup_middlewares
from api.routes import setup_routes
from core.config import settings
from core.database import db_helper
from core.websocket_manager import websocket_manager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    yield
    await db_helper.dispose()
    await websocket_manager.dispose()


app = FastAPI(
    lifespan=lifespan,
    title=settings.api_config.title,
    description=settings.api_config.description,
    version=settings.api_config.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


setup_routes(app, prefix=settings.api_config.prefix)
setup_exceptions(app)
setup_middlewares(app)

if __name__ == "__main__":
    uvicorn.run(app, host=settings.run_config.host, port=settings.run_config.port)
