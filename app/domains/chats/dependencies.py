from typing import Annotated

from core.dependencies import SessionDep
from fastapi import Depends

from domains.chats.repository import ChatRepository
from domains.chats.service import ChatService
from domains.users.repository import UserRepository


async def get_chat_service(
    session: SessionDep,
    chat_repo: Annotated[ChatRepository, Depends(ChatRepository)],
    user_repo: Annotated[UserRepository, Depends(UserRepository)],
) -> ChatService:
    return ChatService(chat_repo, user_repo, session)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
