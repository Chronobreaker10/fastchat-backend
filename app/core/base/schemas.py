from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str
    details: dict


class PaginationParams(BaseModel):
    date: Annotated[datetime, Field(title="Дата сортировки")]
    entity_id: Annotated[int, Field(title="ID сущности")]
    limit: Annotated[int, Field(title="Количество записей на странице", le=100)] = 3
