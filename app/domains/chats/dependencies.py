import uuid
from typing import Annotated

from core.dependencies import SessionDep
from fastapi import Depends, Path

from domains.chats.repository import ChatRepository
from domains.chats.service import ChatService
from domains.messages.repository import MessageRepository
from domains.users.repository import UserRepository


async def get_chat_service(
    session: SessionDep,
    chat_repo: Annotated[ChatRepository, Depends()],
    user_repo: Annotated[UserRepository, Depends()],
    message_repo: Annotated[MessageRepository, Depends()],
) -> ChatService:
    return ChatService(chat_repo, user_repo, message_repo, session)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
ChatUUIDDep = Annotated[uuid.UUID, Path(title="UUID чата")]
