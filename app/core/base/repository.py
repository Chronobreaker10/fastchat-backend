from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings


class BaseRepository[ModelType]:
    """Базовый репозиторий с общими CRUD-операциями"""

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get_by_id(
        self, session: AsyncSession, record_id: int
    ) -> ModelType | None:
        """Получить запись по ID"""
        result = await session.execute(
            select(self.model).where(self.model.id == record_id),
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = settings.default_limit,
    ) -> Sequence[ModelType]:
        """Получить все записи с пагинацией (сортировка по ID для стабильности)"""
        result = await session.execute(
            select(self.model).order_by(self.model.id).offset(skip).limit(limit),
        )
        return result.scalars().all()

    async def create(self, session: AsyncSession, obj_in: BaseModel) -> ModelType:
        """Создать новую запись из Pydantic-схемы"""
        instance = self.model(**obj_in.model_dump())
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def update(
        self,
        session: AsyncSession,
        record_id: int,
        obj_in: BaseModel,
    ) -> ModelType | None:
        """Обновить запись по ID из Pydantic-схемы"""
        instance = await self.get_by_id(session, record_id)
        if instance is None:
            return None
        for key, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, record_id: int) -> bool:
        """Удалить запись по ID"""
        instance = await self.get_by_id(session, record_id)
        if instance is None:
            return False
        await session.delete(instance)
        await session.flush()
        return True
