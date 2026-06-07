from sqlalchemy.ext.asyncio import AsyncSession

from domains.auth.errors import ForbiddenError
from domains.chats.repository import ChatRepository
from domains.messages.repository import MessageRepository
from domains.messages.schemas import MessageCreate, MessageCreateInDB, MessageRead


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        chat_repo: ChatRepository,
        session: AsyncSession,
    ) -> None:
        self.message_repo = message_repo
        self.chat_repo = chat_repo
        self.session = session

    async def send_message(
        self, data: MessageCreate, current_user_id: int
    ) -> MessageRead:
        if not self.chat_repo.is_member(self.session, data.chat_id, current_user_id):
            message = "У вас нет прав на отправку сообщений в этот чат"
            raise ForbiddenError(message)
        data = MessageCreateInDB(**data.model_dump(), sender_id=current_user_id)
        message = await self.message_repo.create(self.session, data)
        await self.session.commit()
        return MessageRead.model_validate(message)
