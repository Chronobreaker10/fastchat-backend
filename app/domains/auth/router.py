from typing import Annotated

from core.base.schemas import MessageResponse
from core.config import settings
from fastapi import APIRouter, Body, Form, Request, Response

from domains.auth.dependencies import AuthServiceDep, CurrentUserDep
from domains.auth.schemas import Token, UserAuth
from domains.shared.utils import get_user_ip
from domains.users.schemas import UserCreate

router = APIRouter(
    prefix="/auth",
    tags=["Авторизация"],
)

_COOKIE_PATH = "/"


def set_cookie(response: Response, key: str, value: str, expires: int) -> None:
    response.set_cookie(
        key,
        value,
        httponly=True,
        samesite="lax",
        secure=settings.run_config.scheme == "https",
        expires=expires,
        path=_COOKIE_PATH,
    )


def set_jwt_cookies(response: Response, token: Token) -> None:
    set_cookie(
        response,
        settings.security.access_token_cookie_name,
        token.access_token,
        settings.security.access_token_expires_seconds,
    )
    set_cookie(
        response,
        settings.security.refresh_token_cookie_name,
        token.refresh_token,
        settings.security.refresh_token_expires_seconds,
    )


@router.post("/token", summary="Аутентификация в приложении", response_model=Token)
async def login_user(
    form_data: Annotated[UserAuth, Form()],
    auth_service: AuthServiceDep,
    response: Response,
    request: Request,
) -> Token:
    user_ip = get_user_ip(request)
    user_agent = request.headers.get("User-Agent")
    token = await auth_service.login_user(
        form_data.username, form_data.password.get_secret_value(), user_ip, user_agent
    )
    set_jwt_cookies(response, token)
    return token


@router.post(
    "/register", summary="Регистрация нового пользователя", response_model=Token
)
async def register_user(
    user_data: Annotated[UserCreate, Body()],
    auth_service: AuthServiceDep,
    response: Response,
    request: Request,
) -> Token:
    user_ip = get_user_ip(request)
    user_agent = request.headers.get("User-Agent")
    token = await auth_service.register_user(user_data, user_ip, user_agent)
    set_jwt_cookies(response, token)
    return token


@router.post("/refresh", summary="Обновление пары токенов", response_model=Token)
async def refresh_tokens(
    refresh_token: Annotated[str, Body(embed=True)],
    auth_service: AuthServiceDep,
    response: Response,
    request: Request,
) -> Token:
    user_ip = get_user_ip(request)
    user_agent = request.headers.get("User-Agent")
    token = await auth_service.refresh_tokens(refresh_token, user_ip, user_agent)
    set_jwt_cookies(response, token)
    return token


@router.post(
    "/logout", summary="Выход из учетной записи", response_model=MessageResponse
)
async def logout_user(
    auth_service: AuthServiceDep,
    current_user: CurrentUserDep,
    response: Response,
) -> MessageResponse:
    await auth_service.logout_user(current_user)
    response.delete_cookie(settings.security.access_token_cookie_name)
    response.delete_cookie(settings.security.refresh_token_cookie_name)
    return MessageResponse(
        message="Вы успешно вышли из аккаунта", details={"user_id": current_user.id}
    )
