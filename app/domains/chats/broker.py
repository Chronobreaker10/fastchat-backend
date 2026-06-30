from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from core.config import settings
from redis.asyncio import Redis

from domains.chats.schemas import ChatWebsocket, ClosedConnectionEvent, WebsocketEvent

if TYPE_CHECKING:
    from core.websocket_manager import WebSocketConnectionManager


class ChatBroker:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def add_user(self, user_id: int, chat_id: UUID) -> None:
        chat_users_key = f"{settings.chat_broker_config.online_users_prefix}:{chat_id}"
        await self.redis.sadd(chat_users_key, user_id)

    async def remove_user(self, user_id: int, chat_id: UUID) -> None:
        chat_users_key = f"{settings.chat_broker_config.online_users_prefix}:{chat_id}"
        await self.redis.srem(chat_users_key, user_id)

    async def is_added(self, user_id: int, chat_id: UUID) -> int:
        chat_users_key = f"{settings.chat_broker_config.online_users_prefix}:{chat_id}"
        return await self.redis.sismember(chat_users_key, str(user_id))

    async def get_online_users(self, chat_id: UUID) -> set[bytes | str]:
        chat_users_key = f"{settings.chat_broker_config.online_users_prefix}:{chat_id}"
        return await self.redis.smembers(chat_users_key)

    async def delete_chat(self, chat_id: UUID) -> None:
        chat_users_key = f"{settings.chat_broker_config.online_users_prefix}:{chat_id}"
        await self.redis.delete(chat_users_key)

    async def publish_chat_event(self, chat_id: UUID, data: WebsocketEvent) -> None:
        await self.redis.publish(
            settings.chat_broker_config.broadcast_channel_key,
            ChatWebsocket(chat_id=chat_id, websocket_data=data).model_dump_json(),
        )

    async def publish_closed_connection(self, data: ClosedConnectionEvent) -> None:
        await self.redis.publish(
            settings.chat_broker_config.closed_connections_key,
            data.model_dump_json(),
        )

    async def subscribe_to_chat_events(
        self, websocket_manager: WebSocketConnectionManager
    ) -> None:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(settings.chat_broker_config.broadcast_channel_key)
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = ChatWebsocket.model_validate_json(message["data"].decode())
                await websocket_manager.chat_broadcast(
                    data.websocket_data, data.chat_id, is_published=True
                )

    async def subscribe_to_closed_connections_event(
        self, websocket_manager: WebSocketConnectionManager
    ) -> None:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(settings.chat_broker_config.closed_connections_key)
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = ClosedConnectionEvent.model_validate_json(
                    message["data"].decode()
                )
                await websocket_manager.close_user_connections_to_chat(
                    data.chat_id,
                    data.user_id,
                    is_published=True,
                    is_removed=data.removed,
                )

    async def add_connection(self, user_id: int, chat_id: UUID) -> None:
        key = f"{settings.chat_broker_config.user_connections_prefix}:{user_id}"
        current_ms = int(time())
        await self.redis.zadd(key, {str(chat_id): current_ms})

    async def remove_connection(self, user_id: int, chat_id: UUID) -> None:
        key = f"{settings.chat_broker_config.user_connections_prefix}:{user_id}"
        await self.redis.zrem(key, str(chat_id))

    async def get_count_user_connections(self, user_id: int) -> int:
        key = f"{settings.chat_broker_config.user_connections_prefix}:{user_id}"
        return await self.redis.zcard(key)

    async def remove_connections_by_rank(self, user_id: int, rank: int) -> None:
        key = f"{settings.chat_broker_config.user_connections_prefix}:{user_id}"
        await self.redis.zremrangebyrank(key, 0, rank)

    async def get_user_connections(
        self, user_id: int, rank: int
    ) -> list[bytes | str] | list[tuple[bytes | str, Any]] | list[list[Any]]:
        key = f"{settings.chat_broker_config.user_connections_prefix}:{user_id}"
        return await self.redis.zrange(key, 0, rank)
