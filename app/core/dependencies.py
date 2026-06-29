from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_helper
from core.redis import get_redis
from core.websocket_manager import WebSocketConnectionManager, get_websocket_manager

SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
WebSocketManagerDep = Annotated[
    WebSocketConnectionManager, Depends(get_websocket_manager)
]
