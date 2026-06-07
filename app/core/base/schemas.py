from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str
    details: dict


class PaginationParams(BaseModel):
    date: Annotated[datetime | None, Field(title="Дата сортировки")] = None
    entity_id: Annotated[int | None, Field(title="ID сущности")] = None
    limit: Annotated[int, Field(title="Количество записей на странице")] = 3
