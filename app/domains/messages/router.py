from core.base.schemas import MessageResponse
from fastapi import APIRouter, status

from domains.auth.dependencies import CurrentUserDep
from domains.messages.dependencies import MessageServiceDep
from domains.messages.schemas import MessageCreate

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
    current_user: CurrentUserDep, service: MessageServiceDep, data: MessageCreate
) -> MessageResponse:
    message = await service.send_message(data, current_user.id)
    return MessageResponse(
        message="Сообщение успешно отправлено", details={"message": message}
    )
