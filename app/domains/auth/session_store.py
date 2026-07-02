from __future__ import annotations

from typing import Protocol

from core.config import settings
from redis.asyncio import Redis

from domains.auth.schemas import UserSession


class SessionStore(Protocol):
    async def save_session(self, key: str, session: UserSession) -> None:
        pass

    async def get_session(self, key: str) -> UserSession | None:
        pass

    async def get_refresh_token(self, user_id: int) -> str | None:
        pass

    async def delete_session(self, key: str) -> None:
        pass

    async def delete_refresh_token(self, user_id: int, key: str) -> None:
        pass


class InMemorySessionStore(SessionStore):
    def __init__(self) -> None:
        self.keys = {}
        self.sessions = {}

    async def save_session(self, key: str, session: UserSession) -> None:
        self.sessions[key] = session
        self.keys[session.user_id] = key

    async def get_refresh_token(self, user_id: int) -> str | None:
        return self.keys.get(user_id)

    async def get_session(self, key: str) -> UserSession | None:
        return self.sessions.get(key)

    async def delete_session(self, key: str) -> None:
        self.sessions.pop(key)

    async def delete_refresh_token(self, user_id: int, key: str) -> None:
        self.sessions.pop(key)
        self.keys.pop(user_id)


class RedisSessionStore(SessionStore):
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def save_session(self, key: str, session: UserSession) -> None:
        token_key = f"{settings.security.refresh_token_store_prefix}:{session.user_id}"
        session_key = f"{settings.security.user_session_store_prefix}:{key}"
        async with self.redis.pipeline(transaction=True) as pipe:
            # noinspection PyAsyncCall
            pipe.set(token_key, key, ex=settings.security.refresh_token_expires_seconds)
            # noinspection PyAsyncCall
            pipe.hset(session_key, mapping=session.model_dump(mode="json"))
            # noinspection PyAsyncCall
            pipe.expire(session_key, settings.security.refresh_token_expires_seconds)
            await pipe.execute()

    async def get_refresh_token(self, user_id: int) -> str | None:
        token_key = f"{settings.security.refresh_token_store_prefix}:{user_id}"
        hash_token = await self.redis.get(token_key)
        return str(hash_token)

    async def get_session(self, key: str) -> UserSession | None:
        session_key = f"{settings.security.user_session_store_prefix}:{key}"
        session = await self.redis.hgetall(session_key)
        if session:
            return UserSession(**session)
        return None

    async def delete_session(self, key: str) -> None:
        session_key = f"{settings.security.user_session_store_prefix}:{key}"
        await self.redis.delete(session_key)

    async def delete_refresh_token(self, user_id: int, key: str) -> None:
        token_key = f"{settings.security.refresh_token_store_prefix}:{user_id}"
        session_key = f"{settings.security.user_session_store_prefix}:{key}"
        async with self.redis.pipeline(transaction=True) as pipe:
            # noinspection PyAsyncCall
            pipe.delete(session_key)
            # noinspection PyAsyncCall
            pipe.delete(token_key)
            await pipe.execute()
