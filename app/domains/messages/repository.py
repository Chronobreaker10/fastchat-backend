from __future__ import annotations

import uuid
from collections.abc import Sequence

from core.base.repository import BaseRepository
from core.base.schemas import PaginationParams
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.config import settings
from domains.messages.models import Message


class MessageRepository(BaseRepository[Message]):
    def __init__(self) -> None:
        super().__init__(Message)

    @staticmethod
    async def get_messages_by_chat_id(
        session: AsyncSession,
        chat_id: uuid.UUID,
        pagination: PaginationParams | None = None,
    ) -> Sequence[Message]:
        query = (
            select(Message)
            .options(joinedload(Message.sender))
            .where(
                Message.chat_id == chat_id,
            )
        )
        # Сортировка KeysetPagination
        # подходит для больших таблиц при бесконечной ленте
        if pagination is not None:
            query = query.where(
                tuple_(Message.created_at, Message.id)
                < (pagination.date, pagination.entity_id)
            )
        result = await session.scalars(
            query.order_by(Message.created_at.desc(), Message.id.desc()).limit(
                pagination.limit if pagination is not None else settings.default_limit
            )
        )
        return result.all()
