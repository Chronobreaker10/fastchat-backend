from typing import Annotated

from core.dependencies import KafkaPublisherDep, SessionDep
from fastapi import Depends

from domains.chats.dependencies import WebSocketManagerDep
from domains.chats.repository import ChatRepository
from domains.messages.repository import MessageRepository
from domains.messages.service import MessageService


async def get_message_service(
    session: SessionDep,
    message_repo: Annotated[MessageRepository, Depends()],
    chat_repo: Annotated[ChatRepository, Depends()],
    publisher: KafkaPublisherDep,
    websocket_manager: WebSocketManagerDep,
) -> MessageService:
    return MessageService(
        message_repo, chat_repo, publisher, websocket_manager, session
    )


MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
