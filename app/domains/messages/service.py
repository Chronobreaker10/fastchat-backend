from core.base.schemas import NotificationCreate
from faststream.kafka.publisher import BatchPublisher
from sqlalchemy.ext.asyncio import AsyncSession

from domains.auth.errors import ForbiddenError
from domains.auth.security import decrypt_message, encrypt_message
from domains.chats.errors import ChatNotFoundError
from domains.chats.repository import ChatRepository
from domains.chats.schemas import ChatEvent, WebsocketEvent
from domains.chats.websocket_manager import ConnectionManager
from domains.messages.errors import MessageNotFoundError
from domains.messages.models import Message
from domains.messages.repository import MessageRepository
from domains.messages.schemas import (
    MessageCreate,
    MessageCreateInDB,
    MessagePayload,
    MessageRead,
    MessageReadWithSender,
    MessageUpdate,
)
from domains.users.schemas import UserRead


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        chat_repo: ChatRepository,
        publisher: BatchPublisher,
        websocket_manager: ConnectionManager,
        session: AsyncSession,
    ) -> None:
        self.message_repo = message_repo
        self.chat_repo = chat_repo
        self.publisher = publisher
        self.websocket_manager = websocket_manager
        self.session = session

    async def _get_message(self, message_id: int) -> Message:
        message = await self.message_repo.get_by_id(self.session, message_id)
        if message is None:
            message = f"Сообщение с ID {message_id} не найдено"
            raise MessageNotFoundError(message)
        return message

    async def send_message(
        self, data: MessageCreate, current_user: UserRead
    ) -> MessageRead:
        chat = await self.chat_repo.get_by_uuid(self.session, data.chat_id)
        if chat is None:
            message = f"Чат с ID {data.chat_id} не найден"
            raise ChatNotFoundError(message)
        if not await self.chat_repo.is_member(
            self.session, data.chat_id, current_user.id
        ):
            message = "У вас нет прав на отправку сообщений в этот чат"
            raise ForbiddenError(message)
        encrypted_data = data.model_copy(update={"text": encrypt_message(data.text)})
        message_in = MessageCreateInDB(
            **encrypted_data.model_dump(exclude={"temp_id"}), sender_id=current_user.id
        )
        message = await self.message_repo.create(self.session, message_in)
        await self.session.commit()
        message = MessageRead.model_validate(message).model_copy(
            update={"text": decrypt_message(message.text)}
        )
        await self.websocket_manager.chat_broadcast(
            WebsocketEvent(
                event=ChatEvent.sent_message,
                payload=MessagePayload(
                    message=MessageReadWithSender(
                        **message.model_dump(), sender=current_user
                    ),
                    temp_id=data.temp_id,
                ),
            ),
            data.chat_id,
        )
        members = await self.chat_repo.get_members_ids(self.session, data.chat_id)
        if len(members) > 1:
            await self.publisher.publish(
                *[
                    NotificationCreate(
                        body="Новое сообщение в чате",
                        chat_id=data.chat_id,
                        chat_name=chat.name,
                        recipient_id=member,
                    ).model_dump(mode="json")
                    for member in members
                    if member != current_user.id
                ]
            )
        return message

    async def update_message(
        self, message_id: int, data: MessageUpdate, current_user: UserRead
    ) -> MessageRead:
        message = await self._get_message(message_id)
        if current_user.id != message.sender_id:
            raise ForbiddenError(
                "У вас нет прав на изменение сообщения " + str(message_id)
            )
        encrypted_data = data.model_copy(update={"text": encrypt_message(data.text)})
        await self.message_repo.update_message(self.session, message, encrypted_data)
        await self.session.commit()
        message = MessageRead.model_validate(message).model_copy(
            update={"text": decrypt_message(message.text)}
        )
        await self.websocket_manager.chat_broadcast(
            WebsocketEvent(
                event=ChatEvent.message_updated,
                payload=MessagePayload(
                    message=MessageReadWithSender(
                        **message.model_dump(), sender=current_user
                    )
                ),
            ),
            message.chat_id,
        )
        return message

    async def delete_message(self, message_id: int, current_user_id: int) -> Message:
        message = await self._get_message(message_id)
        if current_user_id != message.sender_id:
            raise ForbiddenError(
                "У вас нет прав на удаление сообщения " + str(message_id)
            )
        await self.message_repo.delete_message(self.session, message)
        await self.session.commit()
        await self.websocket_manager.chat_broadcast(
            WebsocketEvent(event=ChatEvent.message_deleted, payload=message.id),
            message.chat_id,
        )
        return message

    async def read_message(self, message_id: int, current_user_id: int) -> None:
        message = await self._get_message(message_id)
        if current_user_id == message.sender_id:
            return
        if not await self.chat_repo.is_member(
            self.session, message.chat_id, current_user_id
        ):
            message = "У вас нет прав на чтение сообщений в этом чате"
            raise ForbiddenError(message)
        await self.message_repo.update_messages_status(self.session, [message.id])
        await self.session.commit()
        await self.websocket_manager.chat_broadcast(
            WebsocketEvent(
                event=ChatEvent.read_message,
                payload=[message.id],
            ),
            message.chat_id,
        )
