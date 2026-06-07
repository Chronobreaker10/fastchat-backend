from typing import Annotated

from core.dependencies import SessionDep
from fastapi import Depends

from domains.chats.repository import ChatRepository
from domains.messages.repository import MessageRepository
from domains.messages.service import MessageService


async def get_message_service(
    session: SessionDep,
    message_repo: Annotated[MessageRepository, Depends()],
    chat_repo: Annotated[ChatRepository, Depends()],
) -> MessageService:
    return MessageService(message_repo, chat_repo, session)


MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
