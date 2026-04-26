from __future__ import annotations

import uuid
from collections.abc import Sequence

from core.base.repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from domains.chats.models import Chat, ChatUser


class ChatRepository(BaseRepository[Chat]):
    def __init__(self) -> None:
        super().__init__(Chat)

    @staticmethod
    async def get_by_uuid(session: AsyncSession, chat_uuid: uuid.UUID) -> Chat | None:
        result = await session.execute(
            select(Chat).where(Chat.id == chat_uuid),
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add_member(
        session: AsyncSession, chat_id: uuid.UUID, user_id: int
    ) -> ChatUser:
        chat_user = ChatUser(chat_id=chat_id, user_id=user_id)
        session.add(chat_user)
        await session.flush()
        await session.refresh(chat_user)
        return chat_user

    @staticmethod
    async def is_member(
        session: AsyncSession, chat_id: uuid.UUID, user_id: int
    ) -> bool:
        query = select(ChatUser).where(
            ChatUser.chat_id == chat_id, ChatUser.user_id == user_id
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_chats_by_user_id(
        session: AsyncSession, user_id: int
    ) -> Sequence[Chat]:
        result = await session.execute(
            select(Chat)
            .options(
                joinedload(Chat.creator),
                selectinload(Chat.members).joinedload(ChatUser.user),
            )
            .where(Chat.user_id == user_id),
        )
        return result.scalars().all()
