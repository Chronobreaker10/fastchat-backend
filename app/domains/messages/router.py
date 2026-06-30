from typing import Annotated

from core.base.schemas import MessageResponse
from core.dependencies import WebSocketManagerDep
from fastapi import APIRouter, Path, status

from domains.auth.dependencies import CurrentUserDep
from domains.chats.schemas import ChatEvent, WebsocketEvent
from domains.messages.dependencies import MessageServiceDep
from domains.messages.schemas import MessageCreate, MessageReadWithSender

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
    websocket_manager: WebSocketManagerDep,
) -> MessageResponse:
    message = await service.send_message(data, current_user.id)
    await websocket_manager.chat_broadcast(
        WebsocketEvent(
            event=ChatEvent.sent_message,
            payload=MessageReadWithSender(**message.model_dump(), sender=current_user),
        ),
        data.chat_id,
    )
    return MessageResponse(
        message="Сообщение успешно отправлено", details={"message": message}
    )


@router.delete(
    "/{message_id}", response_model=MessageResponse, summary="Удаление сообщения"
)
async def delete_message(
    current_user: CurrentUserDep,
    service: MessageServiceDep,
    message_id: Annotated[int, Path(title="ID сообщения")],
    websocket_manager: WebSocketManagerDep,
) -> MessageResponse:
    message = await service.delete_message(message_id, current_user.id)
    await websocket_manager.chat_broadcast(
        WebsocketEvent(event=ChatEvent.message_deleted, payload=message.id),
        message.chat_id,
    )
    return MessageResponse(
        message="Сообщение успешно удалено", details={"message_id": message.id}
    )
