from typing import Annotated

from core.base.schemas import MessageResponse
from fastapi import APIRouter, Body, Path, status

from domains.auth.dependencies import CurrentUserDep
from domains.messages.dependencies import MessageServiceDep
from domains.messages.schemas import (
    MessageCreate,
    MessageUpdate,
)

router = APIRouter(
    prefix="/messages",
    tags=["Сообщения"],
)


@router.post(
    "/",
    response_model=MessageResponse,
    summary="Отправка сообщения",
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    current_user: CurrentUserDep,
    service: MessageServiceDep,
    data: MessageCreate,
) -> MessageResponse:
    message = await service.send_message(data, current_user)
    return MessageResponse(
        message="Сообщение успешно отправлено", details={"message": message}
    )


@router.patch(
    "/{message_id}",
    response_model=MessageResponse,
    summary="Редактирование сообщения",
    description="Изменение текста сообщения",
)
async def update_message(
    current_user: CurrentUserDep,
    service: MessageServiceDep,
    message_id: Annotated[int, Path(title="ID сообщения")],
    data: Annotated[MessageUpdate, Body()],
) -> MessageResponse:
    message = await service.update_message(message_id, data, current_user)
    return MessageResponse(
        message="Сообщение успешно изменено", details={"message": message}
    )


@router.delete(
    "/{message_id}", response_model=MessageResponse, summary="Удаление сообщения"
)
async def delete_message(
    current_user: CurrentUserDep,
    service: MessageServiceDep,
    message_id: Annotated[int, Path(title="ID сообщения")],
) -> MessageResponse:
    message = await service.delete_message(message_id, current_user.id)
    return MessageResponse(
        message="Сообщение успешно удалено", details={"message_id": message.id}
    )
