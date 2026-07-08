import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

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


class MessageUpdate(MessageBase):
    pass


class MessageCreateInDB(MessageCreate):
    sender_id: Annotated[int, Field(ge=1, title="ID отправителя сообщения")]


class MessageRead(MessageCreateInDB):
    id: Annotated[int, Field(ge=1, title="ID сообщения")]
    created_at: Annotated[
        datetime,
        Field(title="Время отправки сообщения"),
    ]


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
