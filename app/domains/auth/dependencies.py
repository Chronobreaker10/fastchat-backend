from typing import Annotated

from core.config import settings
from core.dependencies import SessionDep
from fastapi import Cookie, Depends
from fastapi.security import OAuth2PasswordBearer

from domains.auth.errors import UnauthorizedError
from domains.auth.service import AuthService
from domains.users.repository import UserRepository
from domains.users.schemas import UserRead

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


async def get_auth_service(
    session: SessionDep,
    repo: Annotated[UserRepository, Depends(UserRepository)],
) -> AuthService:
    return AuthService(repo, session)


async def get_current_user(
    auth_service: AuthServiceDep,
    auth_header: Annotated[str | None, Depends(oauth2_scheme)] = None,
    auth_cookie: Annotated[
        str | None, Cookie(alias=settings.security.cookie_name)
    ] = None,
) -> UserRead:
    token = None
    if auth_cookie is not None:
        token = auth_cookie
    elif auth_header is not None:
        token = auth_header
    if token is None:
        raise UnauthorizedError
    return await auth_service.get_user_from_token(token)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[UserRead, Depends(get_current_user)]
