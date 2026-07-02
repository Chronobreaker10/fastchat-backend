from __future__ import annotations

from functools import cache
from typing import Protocol

from domains.auth.schemas import UserSession


class SessionStore(Protocol):
    async def save_session(self, key: str, session: UserSession) -> None:
        pass

    async def get_session(self, key: str) -> UserSession | None:
        pass

    async def get_key(self, user_id: int) -> str | None:
        pass

    async def delete_session(self, key: str) -> None:
        pass

    async def delete_key(self, user_id: int) -> None:
        pass


class InMemorySessionStore(SessionStore):
    def __init__(self) -> None:
        self.keys = {}
        self.sessions = {}

    async def save_session(self, key: str, session: UserSession) -> None:
        self.sessions[key] = session
        self.keys[session.user_id] = key

    async def get_key(self, user_id: int) -> str | None:
        return self.keys.get(user_id)

    async def get_session(self, key: str) -> UserSession | None:
        return self.sessions.get(key)

    async def delete_session(self, key: str) -> None:
        self.sessions.pop(key)

    async def delete_key(self, user_id: int) -> None:
        self.keys.pop(user_id)


@cache
def get_session_store() -> SessionStore:
    return InMemorySessionStore()
