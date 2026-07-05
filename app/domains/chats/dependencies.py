import uuid
from typing import Annotated

from core.dependencies import KafkaPublisherDep, RedisDep, SessionDep
from fastapi import Depends, Path

from domains.chats.broker import ChatBroker
from domains.chats.repository import ChatRepository
from domains.chats.service import ChatService
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
) -> ChatService:
    return ChatService(
        chat_repo, user_repo, message_repo, chat_broker, publisher, session
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
ChatBrokerDep = Annotated[ChatBroker, Depends(get_chat_broker)]
ChatUUIDDep = Annotated[uuid.UUID, Path(title="UUID чата")]
