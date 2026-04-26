from typing import Annotated

from core.base.schemas import Token
from core.config import settings
from fastapi import APIRouter, Body, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

from domains.auth.dependencies import AuthServiceDep
from domains.users.schemas import UserCreate

router = APIRouter(
    prefix="/auth",
    tags=["Авторизация"],
)


@router.post("/token", response_model=Token)
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
    response: Response,
) -> Token:
    token = await auth_service.login_user(form_data.username, form_data.password)
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
