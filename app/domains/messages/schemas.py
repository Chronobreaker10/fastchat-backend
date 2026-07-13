from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from domains.messages.models import MessageStatus
from domains.shared.utils import get_msc_dt
from domains.users.schemas import UserRead


class MessageBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: Annotated[
        str,
        Field(min_length=1, max_length=500, title="Текст сообщения"),
    ]


class MessageCreate(MessageBase):
    chat_id: Annotated[
        uuid.UUID,
        Field(
            title="ID чата",
            description="Идентификатор чата, в который отправлено сообщение",
        ),
    ]
    temp_id: Annotated[
        uuid.UUID | None, Field(title="Временный ID для обновления статуса сообщения")
    ] = None


class MessageUpdate(MessageBase):
    pass


class MessageCreateInDB(MessageBase):
    chat_id: Annotated[
        uuid.UUID,
        Field(
            title="ID чата",
            description="Идентификатор чата, в который отправлено сообщение",
        ),
    ]
    sender_id: Annotated[int, Field(ge=1, title="ID отправителя сообщения")]


class MessageRead(MessageCreateInDB):
    id: Annotated[int, Field(ge=1, title="ID сообщения")]
    message_status: Annotated[MessageStatus, Field(title="Статус сообщения")] = (
        MessageStatus.DELIVERED
    )
    created_at: Annotated[
        datetime,
        Field(title="Время отправки сообщения"),
    ]

    @field_serializer("created_at")
    def created_at_to_msc_dt(self, v: datetime) -> datetime:
        return get_msc_dt(v.replace(microsecond=0))


class MessageReadWithSender(MessageRead):
    sender: Annotated[UserRead, Field(title="Отправитель сообщения")]


class MessageReadWithSenderUsername(MessageRead):
    sender_username: Annotated[
        str,
        Field(
            min_length=3,
            max_length=100,
            title="Имя отправителя",
            description="Имя отправителя",
        ),
    ]


class MessagePayload(BaseModel):
    message: Annotated[MessageReadWithSender, Field(title="Новое сообщение")]
    temp_id: Annotated[
        uuid.UUID | None, Field(title="Временный ID для обновления статуса сообщения")
    ] = None
