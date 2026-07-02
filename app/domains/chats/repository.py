from __future__ import annotations

import uuid
from collections.abc import Sequence

from core.base.repository import BaseRepository
from sqlalchemy import RowMapping, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    joinedload,
    selectinload,
)

from domains.chats.models import Chat, ChatUser
from domains.chats.schemas import ChatUpdate
from domains.messages.models import Message
from domains.users.models import User


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
    async def get_with_relationships(
        session: AsyncSession,
        chat_uuid: uuid.UUID,
        with_creator: bool = False,
        with_members: bool = False,
        with_messages: bool = False,
    ) -> Chat | None:
        query = select(Chat)
        if with_creator:
            query = query.options(joinedload(Chat.creator))
        if with_members:
            query = query.options(selectinload(Chat.members).joinedload(ChatUser.user))
        if with_messages:
            query = query.options(
                selectinload(Chat.messages).joinedload(Message.sender)
            )
        result = await session.execute(
            query.where(Chat.id == chat_uuid),
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add_member(
        session: AsyncSession, chat_id: uuid.UUID, user_id: int, invited_id: int
    ) -> ChatUser:
        chat_user = ChatUser(chat_id=chat_id, user_id=user_id, invited_id=invited_id)
        session.add(chat_user)
        await session.flush()
        await session.refresh(chat_user)
        return chat_user

    @staticmethod
    async def delete_member(
        session: AsyncSession, chat_id: uuid.UUID, user_id: int
    ) -> None:
        query = delete(ChatUser).where(
            ChatUser.chat_id == chat_id, ChatUser.user_id == user_id
        )
        await session.execute(query)

    @staticmethod
    async def get_members_ids(
        session: AsyncSession, chat_id: uuid.UUID
    ) -> Sequence[int]:
        query = select(ChatUser.user_id).where(ChatUser.chat_id == chat_id)
        result = await session.execute(query)
        return result.scalars().all()

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
    async def get_chats_by_user_id_with_last_message(
        session: AsyncSession, user_id: int
    ) -> Sequence[RowMapping]:
        row_number = func.row_number().over(
            partition_by=Chat.id, order_by=Message.created_at.desc()
        )
        subquery = (
            select(
                Chat.id,
                Chat.name,
                Chat.user_id,
                Chat.created_at,
                Message.id.label("message_id"),
                Message.text.label("message_text"),
                Message.sender_id.label("sender_id"),
                Message.created_at.label("sent_at"),
                User.username.label("sender_username"),
                row_number.label("row_num"),
            )
            .join(Chat.members)
            .join(Chat.messages, isouter=True)
            .join(Message.sender, isouter=True)
            .where(ChatUser.user_id == user_id)
        ).subquery()
        query = (
            select(subquery)
            .where(subquery.c.row_num == 1)
            .order_by(subquery.c.sent_at.desc().nullslast())
        )
        result = await session.execute(query)
        return result.mappings().all()

    @staticmethod
    async def update_chat(
        session: AsyncSession,
        chat: Chat,
        chat_data: ChatUpdate,
    ) -> Chat:
        for key, value in chat_data.model_dump(exclude_unset=True).items():
            setattr(chat, key, value)
        await session.flush()
        await session.refresh(chat)
        return chat

    @staticmethod
    async def delete_chat(session: AsyncSession, chat: Chat) -> None:
        await session.delete(chat)
        await session.flush()
