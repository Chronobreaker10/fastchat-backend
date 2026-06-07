from typing import Annotated

from core.base.schemas import MessageResponse, PaginationParams
from fastapi import APIRouter, Body, Depends, Path, Query, Request, status

from domains.auth.dependencies import CurrentUserDep
from domains.chats.dependencies import ChatServiceDep, ChatUUIDDep
from domains.chats.schemas import (
    ChatCreate,
    ChatRead,
    ChatUpdate,
    ChatWithMessages,
    InvitesResponse,
)

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
    chat_id: ChatUUIDDep,
    current_user: CurrentUserDep,
    service: ChatServiceDep,
    pagination: Annotated[Query, Depends(PaginationParams)],
) -> ChatWithMessages:
    return await service.get_chat_by_uuid(chat_id, current_user.id, pagination)


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
    chat_name = await service.add_member_to_chat_by_username(
        chat_id, username, current_user.id
    )
    return MessageResponse(
        message=(
            f"Пользователь {current_user.username} добавил {username} в чат {chat_name}"
        ),
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
    chat_name = await service.leave_chat(chat_id, current_user.id)
    return MessageResponse(
        message=f"Пользователь {current_user.username} покинул чат {chat_name}",
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
    chat_name, username = await service.remove_member_from_chat(
        chat_id, user_id, current_user.id
    )
    return MessageResponse(
        message=f"Пользователь {username} удален из чата {chat_name}",
        details={"chat_id": chat_id},
    )


@router.post(
    "/invite",
    response_model=MessageResponse,
    name="join_chat",
    summary="Присоединиться к чату по токену приглашения",
)
async def join_chat_by_invite_link(
    invite_token: Annotated[str, Query(min_length=1, title="Токен приглашения")],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> MessageResponse:
    chat, invited_name = await service.add_member_to_chat_by_invite_token(
        invite_token, current_user.id
    )
    return MessageResponse(
        message=(
            f"Пользователь {current_user.username} "
            f"присоединился к чату {chat.name} "
            f"по приглашению {invited_name}"
        ),
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
    request: Request,
) -> InvitesResponse:
    invite_token, chat_name = await service.generate_invite_token(
        chat_id, current_user.id
    )
    invite_link = request.url_for("join_chat").include_query_params(
        invite_token=invite_token
    )
    return InvitesResponse(link=str(invite_link), chat_name=chat_name)
