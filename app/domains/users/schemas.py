from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
            title="Имя пользователя",
            description="Имя пользователя",
        ),
    ]


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: Annotated[int, Field(ge=1, title="ID", description="ID пользователя")]
    created_at: Annotated[
        datetime,
        Field(
            title="Зарегистрировался",
            description="Зарегистрировался",
        ),
    ]


class UserCreate(UserBase):
    password: Annotated[
        str,
        Field(
            min_length=5,
            max_length=100,
            title="Пароль пользователя",
            description="Пароль пользователя",
        ),
    ]


class UserDB(UserBase):
    hashed_password: Annotated[
        str,
        Field(
            min_length=5,
            max_length=500,
            title="Хэш пароля",
            description="Хэш пароля пользователя",
        ),
    ]
