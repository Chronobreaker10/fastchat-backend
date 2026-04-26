from typing import Annotated

from core.dependencies import SessionDep
from fastapi import Cookie, Depends, Header
from fastapi.security import OAuth2PasswordBearer

from domains.auth.errors import UnauthorizedError
from domains.auth.service import AuthService
from domains.users.repository import UserRepository
from domains.users.schemas import UserRead

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_auth_service(
    session: SessionDep,
    repo: Annotated[UserRepository, Depends(UserRepository)],
) -> AuthService:
    return AuthService(repo, session)


async def get_current_user(
    auth_service: AuthServiceDep,
    auth_header: Annotated[str | None, Header(alias="Authorization")] = None,
    auth_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> UserRead:
    token = None
    if auth_header:
        token_data = auth_header.split()
        token_data_count = 2
        if len(token_data) < token_data_count or token_data[0] != "Bearer":
            raise UnauthorizedError
        token = token_data[1]
    elif auth_cookie:
        token = auth_cookie
    if token is None:
        raise UnauthorizedError
    return await auth_service.get_user_from_token(token)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[UserRead, Depends(get_current_user)]
