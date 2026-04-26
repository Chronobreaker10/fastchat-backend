import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from api.errors import setup_exceptions
from api.middlewares import setup_middlewares
from api.routes import setup_routes
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    yield


app = FastAPI(lifespan=lifespan)

setup_routes(app)
setup_exceptions(app)
setup_middlewares(app)


class Item(BaseModel):
    name: str
    description: str | None


items = [
    Item(name="Plumbus", description="A multi-purpose household device."),
    Item(name="Portal Gun", description="A portal opening device."),
    Item(name="Meeseeks Box", description="A box that summons a Meeseeks."),
]


@app.get("/", response_class=EventSourceResponse)
async def root() -> AsyncIterator[ServerSentEvent]:
    for item in items:
        await asyncio.sleep(2)
        yield ServerSentEvent(event="notification", data=item)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
