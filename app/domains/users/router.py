from fastapi import APIRouter

from domains.auth.dependencies import CurrentUserDep
from domains.users.dependencies import UserServiceDep
from domains.users.schemas import UserRead

router = APIRouter(
    prefix="/users",
    tags=["Пользователи"],
)


@router.get("/me", response_model=UserRead)
async def get_profile(current_user: CurrentUserDep) -> UserRead:
    return current_user


@router.get("/{username}", response_model=UserRead)
async def get_user_by_username(username: str, user_service: UserServiceDep) -> UserRead:
    return await user_service.get_user_by_username(username)
