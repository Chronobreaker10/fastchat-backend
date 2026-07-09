from typing import Annotated

from core.base.schemas import MessageResponse, PaginationParams
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from domains.auth.dependencies import CurrentUserDep
from domains.chats.dependencies import ChatServiceDep, ChatUUIDDep, WebSocketManagerDep
from domains.chats.schemas import (
    ChatCreate,
    ChatRead,
    ChatUpdate,
    ChatWithMessages,
    InvitesResponse,
    UserAction,
    UserEvent,
)
from domains.messages.dependencies import MessageServiceDep
from domains.messages.schemas import MessageReadWithSender

router = APIRouter(
    prefix="/chats",
    tags=["Чаты"],
)


@router.post(
    "/",
    response_model=MessageResponse,
    summary="Создание чата",
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    current_user: CurrentUserDep, service: ChatServiceDep, data: ChatCreate
) -> MessageResponse:
    chat = await service.create_chat(current_user.id, data)
    return MessageResponse(
        message=f"Чат {chat.name} успешно создан!", details={"chat_id": chat.id}
    )


@router.get("/", response_model=list[ChatRead], summary="Получение списка моих чатов.")
async def get_my_chats(
    current_user: CurrentUserDep, service: ChatServiceDep
) -> list[ChatRead]:
    return await service.get_user_chats(current_user.id)


@router.get(
    "/{chat_id}",
    response_model=ChatWithMessages,
    summary="Получение чата по ID с участниками и сообщениями",
)
async def get_chat(
    chat_id: ChatUUIDDep, current_user: CurrentUserDep, service: ChatServiceDep
) -> ChatWithMessages:
    return await service.get_chat_by_uuid(chat_id, current_user.id)


@router.get(
    "/{chat_id}/messages",
    response_model=list[MessageReadWithSender],
    summary="Получение сообщений чата по ID",
)
async def get_chat_messages(
    chat_id: ChatUUIDDep,
    current_user: CurrentUserDep,
    service: ChatServiceDep,
    pagination: Annotated[Query, Depends(PaginationParams)],
) -> list[MessageReadWithSender]:
    return await service.get_messages_by_chat_uuid(chat_id, current_user.id, pagination)


@router.put(
    "/{chat_id}",
    response_model=MessageResponse,
    summary="Редактирование чата",
    description="Изменение названия или владельца чата",
)
async def update_chat(
    chat_id: ChatUUIDDep,
    current_user: CurrentUserDep,
    service: ChatServiceDep,
    data: Annotated[ChatUpdate, Body()],
) -> MessageResponse:
    await service.update_chat(chat_id, data, current_user.id)
    return MessageResponse(
        message=f"Чат {chat_id} успешно изменен", details={"chat_id": chat_id}
    )


@router.delete("/{chat_id}", response_model=MessageResponse, summary="Удаление чата")
async def delete_chat(
    chat_id: ChatUUIDDep,
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> MessageResponse:
    chat = await service.delete_chat(chat_id, current_user.id)
    return MessageResponse(
        message=f"Чат {chat.name} успешно удален", details={"chat_id": chat_id}
    )


@router.post(
    "/{chat_id}/members",
    response_model=MessageResponse,
    summary="Добавить нового участника в чат",
)
async def add_member(
    chat_id: ChatUUIDDep,
    username: Annotated[
        str,
        Body(title="Имя нового участника", min_length=3, max_length=100, embed=True),
    ],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> MessageResponse:
    message = await service.add_member_to_chat_by_username(
        chat_id, username, current_user
    )
    return MessageResponse(
        message=message,
        details={"chat_id": chat_id},
    )


@router.delete(
    "/{chat_id}/members",
    response_model=MessageResponse,
    summary="Покинуть чат",
    description="Если владелец покинет чат, то он будет автоматически закрыт",
)
async def leave_chat(
    chat_id: ChatUUIDDep,
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> MessageResponse:
    message = await service.leave_chat(chat_id, current_user)
    return MessageResponse(
        message=message,
        details={"chat_id": chat_id},
    )


@router.delete(
    "/{chat_id}/members/{user_id}",
    response_model=MessageResponse,
    summary="Удалить пользователя из чата",
)
async def remove_member(
    chat_id: ChatUUIDDep,
    user_id: Annotated[int, Path(ge=1, title="ID пользователя")],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> MessageResponse:
    message = await service.remove_member_from_chat(chat_id, user_id, current_user)
    return MessageResponse(
        message=message,
        details={"chat_id": chat_id},
    )


@router.post(
    "/invite",
    response_model=MessageResponse,
    name="join_chat",
    summary="Присоединиться к чату по токену приглашения",
)
async def join_chat_by_invite_link(
    invite_token: Annotated[
        str, Body(min_length=1, title="Токен приглашения", embed=True)
    ],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> MessageResponse:
    chat, message = await service.add_member_to_chat_by_invite_token(
        invite_token, current_user
    )
    return MessageResponse(
        message=message,
        details={"chat_id": chat.id},
    )


@router.get(
    "/{chat_id}/invite",
    response_model=InvitesResponse,
    summary="Сгенерировать ссылку для приглашения в чат",
)
async def generate_invite_link(
    chat_id: ChatUUIDDep,
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> InvitesResponse:
    invite_token, chat_name = await service.generate_invite_token(
        chat_id, current_user.id
    )
    return InvitesResponse(token=invite_token, chat_name=chat_name)


@router.websocket("/{chat_id}/ws")
async def receive_messages(
    websocket: WebSocket,
    chat_id: ChatUUIDDep,
    current_user: CurrentUserDep,
    service: ChatServiceDep,
    message_service: MessageServiceDep,
    websocket_manager: WebSocketManagerDep,
) -> None:
    if await service.is_member(chat_id, current_user.id):
        await websocket_manager.close_user_connections_to_chat(chat_id, current_user.id)
        await websocket_manager.check_user_limit_connections(current_user.id)
        await websocket_manager.connect_to_chat(websocket, chat_id, current_user.id)
        try:
            while True:
                data = await websocket.receive_json()
                event = UserEvent(**data)
                if event.action == UserAction.message_read:
                    await message_service.read_message(
                        event.payload.message_id, current_user.id
                    )
        except WebSocketDisconnect:
            await websocket_manager.close_connection(
                chat_id, current_user.id, websocket, closed=True
            )
