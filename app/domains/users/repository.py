from __future__ import annotations

from core.base.repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from domains.users.errors import UserAlreadyExistsError
from domains.users.models import User
from domains.users.schemas import UserDB


class UserRepository(BaseRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> User | None:
        query = select(User).filter_by(username=username)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, session: AsyncSession, user_data: UserDB) -> User:
        try:
            return await super().create(session=session, obj_in=user_data)
        except IntegrityError:
            raise UserAlreadyExistsError
