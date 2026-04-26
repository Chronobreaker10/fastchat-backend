from core.base.errors import InvalidCredentialsError
from core.base.schemas import Token
from core.config import settings
from core.security import (
    create_access_token,
    get_password_hash,
    validate_token,
    verify_password,
)
from sqlalchemy.ext.asyncio import AsyncSession

from domains.users.repository import UserRepository
from domains.users.schemas import UserCreate, UserDB, UserRead


class AuthService:
    def __init__(self, repo: UserRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def login_user(self, username: str, password: str) -> Token:
        user = await self.repo.get_by_username(self.session, username)
        if not user:
            verify_password(password, settings.security.default_dump)
            raise InvalidCredentialsError
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError
        access_token = create_access_token(data={"sub": str(user.id)})
        return Token(access_token=access_token)

    async def register_user(self, user_data: UserCreate) -> Token:
        db_user = UserDB(
            **user_data.model_dump(),
            hashed_password=get_password_hash(user_data.password),
        )
        user = await self.repo.create_user(self.session, db_user)
        await self.session.commit()
        access_token = create_access_token(data={"sub": str(user.id)})
        return Token(access_token=access_token)

    async def get_user_from_token(self, token: str) -> UserRead:
        token_data = validate_token(token)
        user = await self.repo.get_by_id(self.session, token_data.user_id)
        if user is None:
            raise InvalidCredentialsError
        return UserRead.model_validate(user)
