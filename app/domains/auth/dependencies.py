from __future__ import annotations

from typing import Annotated

from core.config import settings
from core.dependencies import RedisDep, SessionDep
from fastapi import Cookie, Depends, Header

# from fastapi.security import OAuth2PasswordBearer
from domains.auth.errors import UnauthorizedError
from domains.auth.service import AuthService
from domains.auth.session_store import RedisSessionStore, SessionStore
from domains.users.repository import UserRepository
from domains.users.schemas import UserRead

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


async def get_session_store(
    redis: RedisDep,
) -> SessionStore:
    return RedisSessionStore(redis)


async def get_auth_service(
    session: SessionDep,
    repo: Annotated[UserRepository, Depends(UserRepository)],
    store: Annotated[SessionStore, Depends(get_session_store)],
) -> AuthService:
    return AuthService(repo, store, session)


async def get_current_user(
    auth_service: AuthServiceDep,
    auth_header: Annotated[str | None, Header(alias="Authorization")] = None,
    auth_cookie: Annotated[
        str | None, Cookie(alias=settings.security.access_token_cookie_name)
    ] = None,
) -> UserRead:
    token = None
    if auth_cookie is not None:
        token = auth_cookie
    elif auth_header is not None:
        token = auth_header.split(" ")[-1]
    if token is None:
        raise UnauthorizedError
    return await auth_service.get_user_from_token(token)
    # if auth_cookie is None:
    #     raise UnauthorizedError
    # return await auth_service.get_user_from_token(auth_cookie)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[UserRead, Depends(get_current_user)]
