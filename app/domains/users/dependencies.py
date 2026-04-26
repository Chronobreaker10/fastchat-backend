from typing import Annotated

from core.dependencies import SessionDep
from fastapi import Depends

from domains.users.repository import UserRepository
from domains.users.service import UserService


async def get_user_service(
    session: SessionDep,
    repo: Annotated[UserRepository, Depends(UserRepository)],
) -> UserService:
    return UserService(repo, session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
