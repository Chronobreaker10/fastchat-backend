import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from api.errors import setup_exceptions
from api.middlewares import setup_middlewares
from api.routes import setup_routes
from core.config import settings
from core.database import db_helper
from core.publisher import get_kafka_broker
from core.redis import get_redis
from domains.chats.broker import ChatBroker
from domains.chats.dependencies import get_websocket_manager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    redis = get_redis()
    broker = get_kafka_broker()
    chat_broker = ChatBroker(redis)
    websocket_manager = get_websocket_manager()
    subscribe_messages_task = asyncio.create_task(
        chat_broker.subscribe_to_chat_events(websocket_manager)
    )
    subscribe_closed_connections_task = asyncio.create_task(
        chat_broker.subscribe_to_closed_connections_event(websocket_manager)
    )
    await broker.start()
    yield
    await broker.stop()
    subscribe_messages_task.cancel()
    subscribe_closed_connections_task.cancel()
    await redis.aclose()
    await db_helper.dispose()
    await websocket_manager.dispose()


app = FastAPI(
    lifespan=lifespan,
    title=settings.api_config.title,
    description=settings.api_config.description,
    version=settings.api_config.version,
)
# app.frontend("/", directory="dist")

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
