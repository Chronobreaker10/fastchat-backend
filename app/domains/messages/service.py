from core.base.schemas import NotificationCreate
from faststream.kafka.publisher import BatchPublisher
from sqlalchemy.ext.asyncio import AsyncSession

from domains.auth.errors import ForbiddenError
from domains.auth.security import decrypt_message, encrypt_message
from domains.chats.repository import ChatRepository
from domains.messages.errors import MessageNotFoundError
from domains.messages.models import Message
from domains.messages.repository import MessageRepository
from domains.messages.schemas import MessageCreate, MessageCreateInDB, MessageRead


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        chat_repo: ChatRepository,
        publisher: BatchPublisher,
        session: AsyncSession,
    ) -> None:
        self.message_repo = message_repo
        self.chat_repo = chat_repo
        self.publisher = publisher
        self.session = session

    async def _get_message(self, message_id: int) -> Message:
        message = await self.message_repo.get_by_id(self.session, message_id)
        if message is None:
            message = f"Сообщение с ID {message_id} не найдено"
            raise MessageNotFoundError(message)
        return message

    async def send_message(
        self, data: MessageCreate, current_user_id: int
    ) -> MessageRead:
        if not await self.chat_repo.is_member(
            self.session, data.chat_id, current_user_id
        ):
            message = "У вас нет прав на отправку сообщений в этот чат"
            raise ForbiddenError(message)
        encrypted_data = data.model_copy(update={"text": encrypt_message(data.text)})
        data = MessageCreateInDB(
            **encrypted_data.model_dump(), sender_id=current_user_id
        )
        message = await self.message_repo.create(self.session, data)
        await self.session.commit()
        members = await self.chat_repo.get_members_ids(self.session, data.chat_id)
        await self.publisher.publish(
            *[
                NotificationCreate(
                    body="Новое сообщение в чате",
                    chat_id=data.chat_id,
                    recipient_id=member,
                ).model_dump(mode="json")
                for member in members
            ]
        )
        return MessageRead.model_validate(message).model_copy(
            update={"text": decrypt_message(message.text)}
        )

    async def delete_message(self, message_id: int, current_user_id: int) -> Message:
        message = await self._get_message(message_id)
        if current_user_id != message.sender_id:
            raise ForbiddenError("У вас нет прав на удаление чата " + str(message_id))
        await self.message_repo.delete_message(self.session, message)
        await self.session.commit()
        return message
