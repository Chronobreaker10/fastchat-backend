import uuid
from typing import Annotated

from core.base.schemas import Message
from fastapi import APIRouter, Body, Path, status

from domains.auth.dependencies import CurrentUserDep
from domains.chats.dependencies import ChatServiceDep
from domains.chats.schemas import ChatCreate, ChatRead, ChatUpdate

router = APIRouter(
    prefix="/chats",
    tags=["Чаты"],
)


@router.post(
    "/",
    response_model=Message,
    summary="Создание чата",
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    current_user: CurrentUserDep, service: ChatServiceDep, data: ChatCreate
) -> Message:
    chat = await service.create_chat(current_user.id, data)
    return Message(
        message=f"Чат {chat.name} успешно создан!", details={"chat_id": chat.id}
    )


@router.get("/", response_model=list[ChatRead], summary="Получение списка моих чатов.")
async def get_my_chats(
    current_user: CurrentUserDep, service: ChatServiceDep
) -> list[ChatRead]:
    return await service.get_user_chats(current_user.id)


@router.put(
    "/{chat_id}",
    response_model=Message,
    summary="Редактирование чата",
    description="Изменение названия или владельца чата",
)
async def update_chat(
    chat_id: Annotated[uuid.UUID, Path(title="UUID чата")],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
    data: Annotated[ChatUpdate, Body()],
) -> Message:
    await service.update_chat(chat_id, data, current_user.id)
    return Message(message="Чат успешно изменен", details={"chat_id": chat_id})


@router.delete("/{chat_id}", response_model=Message, summary="Удаление чата")
async def delete_chat(
    chat_id: Annotated[uuid.UUID, Path(title="UUID чата")],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> Message:
    chat = await service.delete_chat(chat_id, current_user.id)
    return Message(
        message=f"Чат {chat.name} успешно удален", details={"chat_id": chat_id}
    )


@router.post(
    "/{chat_id}/members",
    response_model=Message,
    summary="Добавить нового участника в чат",
)
async def add_member(
    chat_id: Annotated[uuid.UUID, Path(title="UUID чата")],
    username: Annotated[
        str,
        Body(title="Имя нового участника", min_length=3, max_length=100, embed=True),
    ],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> Message:
    chat_name = await service.add_member_to_chat_by_username(
        chat_id, username, current_user.id
    )
    return Message(
        message=f"Пользователь {username} успешно добавлен в чат {chat_name}",
        details={"chat_id": chat_id},
    )


@router.delete(
    "/{chat_id}/members",
    response_model=Message,
    summary="Покинуть чат",
    description="Если владелец покинет чат, то он будет автоматически закрыт",
)
async def leave_chat(
    chat_id: Annotated[uuid.UUID, Path(title="UUID чата")],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> Message:
    chat_name = await service.leave_chat(chat_id, current_user.id)
    return Message(
        message=f"Вы успешно покинули чат {chat_name}", details={"chat_id": chat_id}
    )


@router.delete(
    "/{chat_id}/members/{user_id}",
    response_model=Message,
    summary="Удалить пользователя из чата",
)
async def remove_member(
    chat_id: Annotated[uuid.UUID, Path(title="UUID чата")],
    user_id: Annotated[int, Path(ge=1, title="ID пользователя")],
    current_user: CurrentUserDep,
    service: ChatServiceDep,
) -> Message:
    chat_name, username = await service.remove_member_from_chat(
        chat_id, user_id, current_user.id
    )
    return Message(
        message=f"Пользователь {username} успешно удален из чата {chat_name}",
        details={"chat_id": chat_id},
    )
