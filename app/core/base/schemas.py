from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class MessageResponse(BaseModel):
    message: Annotated[
        str, Field(title="Сообщение ответа", min_length=1, max_length=500)
    ]
    details: Annotated[dict[str, Any], Field(title="Детали ответа")]


class PaginationParams(BaseModel):
    date: Annotated[datetime, Field(title="Дата сортировки")]
    entity_id: Annotated[int, Field(title="ID сущности")]
    limit: Annotated[int, Field(title="Количество записей на странице", le=100)] = 10


class NotificationCreate(BaseModel):
    body: Annotated[str, Field(min_length=1, max_length=500, title="Текст уведомления")]
    created_at: Annotated[
        datetime,
        Field(
            title="Время отправки уведомления",
            default_factory=lambda: datetime.now(UTC),
        ),
    ]
    chat_id: Annotated[UUID, Field(title="Идентификатор связанного чата")]
    chat_name: Annotated[
        str,
        Field(min_length=3, max_length=100, title="Имя чата", description="Имя чата"),
    ]
    recipient_id: Annotated[int, Field(ge=1, title="Идентификатор получателя")]

    @field_serializer("chat_id")
    def convert_chat_id(self, value: UUID) -> str:
        return str(value)
