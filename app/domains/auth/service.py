from __future__ import annotations

import asyncio
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address, ip_address

from sqlalchemy.ext.asyncio import AsyncSession

from domains.auth.errors import (
    InvalidCredentialsError,
    InvalidIPAddressError,
    UnauthorizedError,
)
from domains.auth.schemas import Token, UserSession
from domains.auth.security import (
    create_jwt_token,
    generate_refresh_token,
    get_dummy_hash,
    get_password_hash,
    hash_token,
    validate_token,
    verify_password,
)
from domains.auth.session_store import SessionStore
from domains.users.repository import UserRepository
from domains.users.schemas import UserCreate, UserDB, UserRead


class AuthService:
    def __init__(
        self, repo: UserRepository, store: SessionStore, session: AsyncSession
    ) -> None:
        self.repo = repo
        self.store = store
        self.session = session

    async def _create_session(self, user_session: UserSession) -> str:
        refresh_token = generate_refresh_token()
        refresh_token_hash = hash_token(refresh_token)
        await self.store.save_session(refresh_token_hash, user_session)
        return refresh_token

    async def _update_session(self, user_session: UserSession) -> str:
        if old_refresh_token := await self.store.get_refresh_token(
            user_session.user_id
        ):
            await self.store.delete_session(old_refresh_token)
        return await self._create_session(user_session)

    @staticmethod
    def _convert_ip(ip: str) -> IPv4Address | IPv6Address:
        try:
            return ip_address(ip)
        except ValueError:
            raise InvalidIPAddressError

    async def login_user(
        self, username: str, password: str, ip: str, user_agent: str | None
    ) -> Token:
        user = await self.repo.get_by_username(self.session, username)
        if not user:
            await asyncio.to_thread(verify_password, password, get_dummy_hash())
            raise InvalidCredentialsError
        if not await asyncio.to_thread(verify_password, password, user.hashed_password):
            raise InvalidCredentialsError
        access_token = create_jwt_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "user_registered_at": user.created_at.isoformat(),
            }
        )
        user_ip = self._convert_ip(ip)
        refresh_token = await self._update_session(
            UserSession(user_id=user.id, ip=user_ip, user_agent=user_agent)
        )
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def register_user(
        self, user_data: UserCreate, ip: str, user_agent: str | None
    ) -> Token:
        hashed_password = await asyncio.to_thread(get_password_hash, user_data.password)
        db_user = UserDB(
            **user_data.model_dump(),
            hashed_password=hashed_password,
        )
        user = await self.repo.create_user(self.session, db_user)
        await self.session.commit()
        access_token = create_jwt_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "user_registered_at": user.created_at.isoformat(),
            }
        )
        user_ip = self._convert_ip(ip)
        refresh_token = await self._update_session(
            UserSession(user_id=user.id, ip=user_ip, user_agent=user_agent)
        )
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh_tokens(
        self, refresh_token: str, ip: str, user_agent: str | None
    ) -> Token:
        refresh_token_hash = hash_token(refresh_token)
        user_session = await self.store.get_session(refresh_token_hash)
        if not user_session:
            raise UnauthorizedError
        user = await self.repo.get_by_id(self.session, user_session.user_id)
        if user is None:
            raise InvalidCredentialsError
        access_token = create_jwt_token(
            data={
                "sub": str(user_session.user_id),
                "username": user.username,
                "user_registered_at": user.created_at.isoformat(),
            }
        )
        user_ip = self._convert_ip(ip)
        await self.store.delete_session(refresh_token_hash)
        refresh_token = await self._create_session(
            UserSession(user_id=user_session.user_id, ip=user_ip, user_agent=user_agent)
        )
        return Token(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    async def get_user_from_token(access_token: str) -> UserRead:
        token_data = validate_token(access_token)
        # user = await self.repo.get_by_id(self.session, int(token_data.sub))
        if token_data.username is None or token_data.user_registered_at is None:
            raise UnauthorizedError
        return UserRead(
            id=int(token_data.sub),
            username=token_data.username,
            created_at=datetime.fromisoformat(token_data.user_registered_at),
        )

    async def logout_user(self, user: UserRead) -> None:
        if refresh_token := await self.store.get_refresh_token(user.id):
            # await self.store.delete_session(refresh_token)
            await self.store.delete_refresh_token(user.id, refresh_token)
