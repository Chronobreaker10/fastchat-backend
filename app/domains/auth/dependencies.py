from typing import Annotated

from core.dependencies import SessionDep
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

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
    token: Annotated[str, Depends(oauth2_scheme)], auth_service: AuthServiceDep
) -> UserRead:
    return await auth_service.get_user_from_token(token)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[UserRead, Depends(get_current_user)]
