import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, SecretStr, field_serializer, field_validator


class TokenType(StrEnum):
    ACCESS = "access_token"
    CHAT_INVITE_LINK = "chat_invite_link"


class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class TokenData(BaseModel):
    user_id: Annotated[int, Field(ge=1, title="ID", description="ID")]


class JWTTokenPayload(BaseModel):
    sub: Annotated[int | uuid.UUID, Field(title="Уникальный идентификатор сущности")]
    iss: Annotated[int | None, Field(title="Издатель токена", ge=1)] = None
    exp: Annotated[datetime, Field(title="Время истечения срока действия токена")]
    type: Annotated[
        TokenType,
        Field(title="Тип токена", description="С какой целью был выпущен токен"),
    ]

    @field_validator("exp")
    @classmethod
    def check_exp_gt_now(cls, v: datetime) -> datetime:
        if v < datetime.now():
            msg = "Expiration time must be greater than now"
            raise ValueError(msg)
        return v

    @field_serializer("iss")
    def get_iss_str_value(self, v: int) -> str:
        return str(v)

    @field_serializer("sub")
    def get_sub_str_value(self, v: int) -> str:
        return str(v)


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
        SecretStr,
        Field(
            min_length=3,
            max_length=100,
            title="Пароль пользователя",
            description="Пароль пользователя",
        ),
    ]
