import uuid
from functools import cache
from typing import Annotated

from core.dependencies import KafkaPublisherDep, RedisDep, SessionDep
from core.redis import get_redis
from fastapi import Depends, Path

from domains.chats.broker import ChatBroker
from domains.chats.repository import ChatRepository
from domains.chats.service import ChatService
from domains.chats.websocket_manager import (
    ConnectionManager,
    WebSocketConnectionManager,
)
from domains.messages.repository import MessageRepository
from domains.users.repository import UserRepository


async def get_chat_broker(
    redis: RedisDep,
) -> ChatBroker:
    return ChatBroker(redis)


async def get_chat_service(
    session: SessionDep,
    chat_repo: Annotated[ChatRepository, Depends()],
    user_repo: Annotated[UserRepository, Depends()],
    message_repo: Annotated[MessageRepository, Depends()],
    chat_broker: Annotated[ChatBroker, Depends(get_chat_broker)],
    publisher: KafkaPublisherDep,
    websocket_manager: WebSocketManagerDep,
) -> ChatService:
    return ChatService(
        chat_repo,
        user_repo,
        message_repo,
        chat_broker,
        publisher,
        websocket_manager,
        session,
    )


@cache
def get_websocket_manager() -> ConnectionManager:
    broker = get_redis()
    return WebSocketConnectionManager(broker)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
ChatBrokerDep = Annotated[ChatBroker, Depends(get_chat_broker)]
ChatUUIDDep = Annotated[uuid.UUID, Path(title="UUID чата")]
WebSocketManagerDep = Annotated[ConnectionManager, Depends(get_websocket_manager)]
