from sqlalchemy.ext.asyncio import AsyncSession

from domains.users.errors import UserNotFoundError
from domains.users.repository import UserRepository
from domains.users.schemas import UserRead


class UserService:
    def __init__(self, repo: UserRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def get_user_by_username(self, username: str) -> UserRead:
        user = await self.repo.get_by_username(self.session, username)
        if user is None:
            raise UserNotFoundError
        return UserRead.model_validate(user)
