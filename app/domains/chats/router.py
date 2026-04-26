from core.base.schemas import Message
from fastapi import APIRouter

from domains.auth.dependencies import CurrentUserDep
from domains.chats.dependencies import ChatServiceDep
from domains.chats.schemas import ChatCreate, ChatRead

router = APIRouter(
    prefix="/chats",
    tags=["Чаты"],
)


@router.post("/", response_model=Message)
async def create_chat(
    current_user: CurrentUserDep, service: ChatServiceDep, data: ChatCreate
) -> Message:
    chat = await service.create_chat(current_user.id, data)
    return Message(message=f"Чат {chat.name} успешно создан!")


@router.get("/", response_model=list[ChatRead])
async def get_my_chats(
    current_user: CurrentUserDep, service: ChatServiceDep
) -> list[ChatRead]:
    return await service.get_user_chats(current_user.id)
