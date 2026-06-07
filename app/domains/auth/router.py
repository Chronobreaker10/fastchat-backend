from typing import Annotated

from core.base.schemas import MessageResponse
from core.config import settings
from fastapi import APIRouter, Body, Form, Response

from domains.auth.dependencies import AuthServiceDep, CurrentUserDep
from domains.auth.schemas import Token, UserAuth
from domains.users.schemas import UserCreate

router = APIRouter(
    prefix="/auth",
    tags=["Авторизация"],
)


@router.post("/token", response_model=Token)
async def login_user(
    form_data: Annotated[UserAuth, Form()],
    auth_service: AuthServiceDep,
    response: Response,
) -> Token:
    token = await auth_service.login_user(
        form_data.username, form_data.password.get_secret_value()
    )
    response.set_cookie(
        "access_token",
        token.access_token,
        httponly=True,
        samesite="lax",
        expires=settings.security.expires_minutes * 60,
    )
    return token


@router.post("/register", response_model=Token)
async def register_user(
    user_data: Annotated[UserCreate, Body(embed=True)],
    auth_service: AuthServiceDep,
    response: Response,
) -> Token:
    token = await auth_service.register_user(user_data)
    response.set_cookie(
        "access_token",
        token.access_token,
        httponly=True,
        samesite="lax",
        expires=settings.security.expires_minutes * 60,
    )
    return token


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    current_user: CurrentUserDep,
    response: Response,
) -> MessageResponse:
    response.delete_cookie("access_token")
    return MessageResponse(
        message="Вы успешно вышли из аккаунта", details={"user_id": current_user.id}
    )
