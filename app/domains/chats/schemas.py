import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from domains.users.schemas import UserRead


class ChatBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Annotated[
        str,
        Field(min_length=3, max_length=100, title="Имя чата", description="Имя чата"),
    ]


class ChatCreate(ChatBase):
    pass


class ChatCreateInDB(ChatCreate):
    user_id: int


class ChatUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user: Annotated[UserRead, Field(title="Участник чата", description="Участник чата")]
    joined_at: Annotated[
        datetime,
        Field(title="Дата добавления", description="Когда участник был добавлен в чат"),
    ]


class ChatRead(ChatBase):
    id: Annotated[
        uuid.UUID,
        Field(
            title="ID чата", description="Уникальный идентификатор чата в формате UUID"
        ),
    ]
    creator: Annotated[
        UserRead,
        Field(title="Создатель чата", description="Создавший этот чат пользователь"),
    ]
    members: Annotated[
        list[ChatUser],
        Field(title="Участники чата", description="Список участников чата"),
    ]
