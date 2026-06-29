from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from domains.messages.schemas import (
    MessageReadWithSender,
    MessageReadWithSenderUsername,
)
from domains.users.schemas import UserRead


class ChatEvent(StrEnum):
    sent_message = "sent_message"
    left_user = "left_user"
    joined_user = "joined_user"
    message_deleted = "message_deleted"


class ChatBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Annotated[
        str,
        Field(min_length=3, max_length=100, title="Имя чата", description="Имя чата"),
    ]


class ChatCreate(ChatBase):
    pass


class ChatUpdate(ChatBase):
    name: Annotated[
        str | None,
        Field(min_length=3, max_length=100, title="Имя чата", description="Имя чата"),
    ] = None
    user_id: Annotated[
        int | None, Field(ge=1, title="ID владельца", alias="owner_id")
    ] = None


class ChatCreateInDB(ChatCreate):
    user_id: int


class ChatUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user: Annotated[UserRead, Field(title="Участник чата", description="Участник чата")]
    joined_at: Annotated[
        datetime,
        Field(title="Дата добавления", description="Когда участник был добавлен в чат"),
    ]
    invited_id: Annotated[
        int | None,
        Field(ge=1, title="ID пользователя, пригласившего в чат"),
    ]


class ChatRead(ChatBase):
    id: Annotated[
        uuid.UUID,
        Field(
            title="ID чата", description="Уникальный идентификатор чата в формате UUID"
        ),
    ]
    # creator: Annotated[
    #     UserRead,
    #     Field(title="Создатель чата", description="Создавший этот чат пользователь"),
    # ]
    # members: Annotated[
    #     list[ChatUser],
    #     Field(title="Участники чата", description="Список участников чата"),
    # ]
    created_at: Annotated[
        datetime,
        Field(title="Время создания чата"),
    ]
    last_message: Annotated[
        MessageReadWithSenderUsername | None, Field(title="Последнее сообщение")
    ] = None


class ChatInDB(ChatCreate):
    id: uuid.UUID
    user_id: int
    created_at: datetime


class ChatWithMembers(ChatInDB):
    members: Annotated[
        list[ChatUser],
        Field(title="Участники чата", description="Список участников чата"),
    ]


class ChatWithMessages(ChatWithMembers):
    id: Annotated[
        uuid.UUID,
        Field(
            title="ID чата", description="Уникальный идентификатор чата в формате UUID"
        ),
    ]
    messages: Annotated[
        list[MessageReadWithSender],
        Field(
            title="Сообщения чата",
            description="Список сообщений чата",
            default_factory=list,
        ),
    ]
    created_at: Annotated[
        datetime,
        Field(title="Время создания чата"),
    ]
    total_messages: Annotated[
        int,
        Field(
            title="Количество сообщений",
            description="Количество сообщений в чате",
            ge=0,
        ),
    ] = 0


class InvitesResponse(BaseModel):
    token: Annotated[str, Field(title="Ссылка-приглашение")]
    chat_name: Annotated[str, Field(title="Название чата")]


class WebsocketEvent(BaseModel):
    event: ChatEvent
    payload: MessageReadWithSender | str | int
    details: Any | None = None


class ChatWebsocket(BaseModel):
    chat_id: uuid.UUID
    websocket_data: WebsocketEvent
