from typing import Annotated

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class TokenData(BaseModel):
    user_id: Annotated[int, Field(ge=1, title="ID", description="ID")]


class UserAuth(BaseModel):
    username: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
            title="Имя пользователя",
            description="Учетное имя пользователя",
        ),
    ]
    password: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
            title="Пароль пользователя",
            description="Пароль пользователя",
        ),
    ]
