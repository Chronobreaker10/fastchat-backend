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

_COOKIE_PATH = "/"


def set_jwt_cookie(response: Response, token: Token) -> None:
    response.set_cookie(
        settings.security.cookie_name,
        token.access_token,
        httponly=True,
        samesite="lax",
        secure=settings.run_config.scheme == "https",
        expires=settings.security.expires_minutes * 60,
        path=_COOKIE_PATH,
    )


@router.post("/token", summary="Аутентификация в приложении", response_model=Token)
async def login_user(
    form_data: Annotated[UserAuth, Form()],
    auth_service: AuthServiceDep,
    response: Response,
) -> Token:
    token = await auth_service.login_user(
        form_data.username, form_data.password.get_secret_value()
    )
    set_jwt_cookie(response, token)
    return token


@router.post(
    "/register", summary="Регистрация нового пользователя", response_model=Token
)
async def register_user(
    user_data: Annotated[UserCreate, Body(embed=True)],
    auth_service: AuthServiceDep,
    response: Response,
) -> Token:
    token = await auth_service.register_user(user_data)
    set_jwt_cookie(response, token)
    return token


@router.post(
    "/logout", summary="Выход из учетной записи", response_model=MessageResponse
)
async def logout_user(
    current_user: CurrentUserDep,
    response: Response,
) -> MessageResponse:
    response.delete_cookie(settings.security.cookie_name)
    return MessageResponse(
        message="Вы успешно вышли из аккаунта", details={"user_id": current_user.id}
    )
