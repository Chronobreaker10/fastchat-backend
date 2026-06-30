from __future__ import annotations

import uuid

from core.base.schemas import PaginationParams
from sqlalchemy.ext.asyncio import AsyncSession

from domains.auth.errors import ForbiddenError
from domains.auth.schemas import TokenType
from domains.auth.security import create_jwt_token, decrypt_message, validate_token
from domains.chats.broker import ChatBroker
from domains.chats.errors import (
    AlreadyMemberChatError,
    AlreadyNotMemberChatError,
    ChatNotFoundError,
)
from domains.chats.models import Chat
from domains.chats.repository import ChatRepository
from domains.chats.schemas import (
    ChatCreate,
    ChatCreateInDB,
    ChatRead,
    ChatUpdate,
    ChatWithMembers,
    ChatWithMessages,
)
from domains.messages.repository import MessageRepository
from domains.messages.schemas import (
    MessageReadWithSender,
    MessageReadWithSenderUsername,
)
from domains.users.errors import UserNotFoundError
from domains.users.models import User
from domains.users.repository import UserRepository


class ChatService:
    def __init__(
        self,
        chat_repo: ChatRepository,
        user_repo: UserRepository,
        message_repo: MessageRepository,
        chat_broker: ChatBroker,
        session: AsyncSession,
    ) -> None:
        self.chat_repo = chat_repo
        self.user_repo = user_repo
        self.message_repo = message_repo
        self.session = session
        self.chat_broker = chat_broker

    async def _get_chat(
        self, chat_id: uuid.UUID, with_creator: bool = False, with_members: bool = False
    ) -> Chat:
        if with_creator or with_members:
            chat = await self.chat_repo.get_with_relationships(
                self.session, chat_id, with_creator, with_members
            )
        else:
            chat = await self.chat_repo.get_by_uuid(self.session, chat_id)
        if chat is None:
            message = f"Чат с ID {chat_id} не найден"
            raise ChatNotFoundError(message)
        return chat

    async def _get_user(self, user_id: int) -> User:
        user = await self.user_repo.get_by_id(self.session, user_id)
        if user is None:
            message = f"Пользователь с ID {user_id} не найден"
            raise UserNotFoundError(message)
        return user

    async def add_member_to_chat(
        self, chat_id: uuid.UUID, user_id: int, invited_id: int
    ) -> None:
        await self._get_user(user_id)
        chat = await self._get_chat(chat_id, with_members=True)
        # if await self.chat_repo.is_member(self.session, chat_id, user_id):
        if user_id in [member.user.id for member in chat.members]:
            raise AlreadyMemberChatError
        await self.chat_repo.add_member(self.session, chat_id, user_id, invited_id)
        await self.session.commit()

    async def add_member_to_chat_by_username(
        self, chat_id: uuid.UUID, username: str, current_user_id: int
    ) -> tuple[str, User]:
        chat = await self._get_chat(chat_id, with_members=True)
        # if not await self.chat_repo.is_member(self.session, chat_id, current_user_id):
        if current_user_id not in [member.user.id for member in chat.members]:
            raise ForbiddenError(
                "У вас нет прав на добавление участника в чат " + str(chat_id)
            )
        user = await self.user_repo.get_by_username(self.session, username)
        if user is None:
            message = f"Пользователь с именем {username} не найден"
            raise UserNotFoundError(message)
        # if await self.chat_repo.is_member(self.session, chat_id, user.id):
        if user.id in [member.user.id for member in chat.members]:
            message = f"Пользователь {username} уже добавлен в чат {chat.name}"
            raise AlreadyMemberChatError(message)
        await self.chat_repo.add_member(self.session, chat_id, user.id, current_user_id)
        await self.session.commit()
        return chat.name, user

    async def remove_member_from_chat(
        self, chat_id: uuid.UUID, user_id: int, current_user_id: int
    ) -> tuple[str, str]:
        chat = await self._get_chat(chat_id, with_creator=True, with_members=True)
        if current_user_id != chat.creator.id:
            raise ForbiddenError(
                "У вас нет прав на удаление пользователей из чата " + str(chat_id)
            )
        user = await self._get_user(user_id)
        # if not await self.chat_repo.is_member(self.session, chat_id, user.id):
        if user.id not in [member.user.id for member in chat.members]:
            message = f"Пользователя с ID {user_id} нет в чате {chat.name}"
            raise AlreadyNotMemberChatError(message)
        await self.chat_repo.delete_member(self.session, chat_id, user.id)
        await self.session.commit()
        return chat.name, user.username

    async def create_chat(self, creator_id: int, data: ChatCreate) -> Chat:
        chat_data = ChatCreateInDB(user_id=creator_id, **data.model_dump())
        chat = await self.chat_repo.create(self.session, chat_data)
        await self.add_member_to_chat(chat.id, creator_id, creator_id)
        return chat

    async def update_chat(
        self, chat_id: uuid.UUID, chat_data: ChatUpdate, current_user_id: int
    ) -> None:
        chat = await self._get_chat(chat_id, with_creator=True, with_members=True)
        if current_user_id != chat.creator.id:
            raise ForbiddenError(
                "У вас нет прав на редактирование чата " + str(chat_id)
            )
        if chat_data.user_id is not None:
            user = await self._get_user(chat_data.user_id)
            if user not in [member.user for member in chat.members]:
                message = f"Пользователя с ID {user.id} нет в чате {chat.name}"
                raise AlreadyNotMemberChatError(message)
        await self.chat_repo.update_chat(self.session, chat, chat_data)
        await self.session.commit()

    async def delete_chat(self, chat_id: uuid.UUID, current_user_id: int) -> Chat:
        chat = await self._get_chat(chat_id, with_creator=True)
        if current_user_id != chat.creator.id:
            raise ForbiddenError("У вас нет прав на удаление чата " + str(chat_id))
        await self.chat_repo.delete_chat(self.session, chat)
        await self.session.commit()
        await self.chat_broker.delete_chat(chat_id)
        return chat

    async def leave_chat(self, chat_id: uuid.UUID, current_user_id: int) -> str:
        chat = await self._get_chat(chat_id, with_creator=True)
        if not await self.chat_repo.is_member(self.session, chat_id, current_user_id):
            raise AlreadyNotMemberChatError("Вас нет в чате " + chat.name)
        if current_user_id == chat.creator.id:
            await self.chat_repo.delete_chat(self.session, chat)
        else:
            await self.chat_repo.delete_member(self.session, chat_id, current_user_id)
        await self.session.commit()
        return chat.name

    async def get_user_chats(self, user_id: int) -> list[ChatRead]:
        chats = await self.chat_repo.get_chats_by_user_id_with_last_message(
            self.session, user_id
        )
        result = []
        for chat in chats:
            last_message = None
            if chat["message_id"]:
                last_message = MessageReadWithSenderUsername(
                    id=chat["message_id"],
                    created_at=chat["sent_at"],
                    sender_id=chat["sender_id"],
                    text=decrypt_message(chat["message_text"]),
                    chat_id=chat["id"],
                    sender_username=chat["sender_username"],
                )
            result.append(ChatRead(**chat, last_message=last_message))
        return result

    async def get_chat_by_uuid(
        self, chat_id: uuid.UUID, current_user_id: int
    ) -> ChatWithMessages:
        chat = await self._get_chat(chat_id, with_members=True)
        if current_user_id not in [member.user.id for member in chat.members]:
            raise ForbiddenError("Вы не являетесь участником чата " + str(chat_id))
        messages = await self.message_repo.get_messages_by_chat_id(
            self.session, chat_id
        )
        messages = [
            MessageReadWithSender.model_validate(message).model_copy(
                update={"text": decrypt_message(message.text)}
            )
            for message in messages
        ]
        messages.reverse()
        count_messages = await self.message_repo.get_total_messages_count_by_chat_id(
            self.session, chat_id
        )
        online_members = await self.chat_broker.get_online_users(chat.id)
        return ChatWithMessages(
            **ChatWithMembers.model_validate(chat).model_dump(),
            messages=messages,
            total_messages=count_messages,
            online_members=[int(member) for member in online_members],
        )

    async def get_messages_by_chat_uuid(
        self, chat_id: uuid.UUID, current_user_id: int, pagination: PaginationParams
    ) -> list[MessageReadWithSender]:
        chat = await self._get_chat(chat_id, with_members=True)
        if current_user_id not in [member.user.id for member in chat.members]:
            raise ForbiddenError("Вы не являетесь участником чата " + str(chat_id))
        messages = await self.message_repo.get_messages_by_chat_id(
            self.session, chat_id, pagination
        )
        messages = [
            MessageReadWithSender.model_validate(message).model_copy(
                update={"text": decrypt_message(message.text)}
            )
            for message in messages
        ]
        messages.reverse()
        return messages

    async def generate_invite_token(
        self, chat_id: uuid.UUID, current_user_id: int
    ) -> tuple[str, str]:
        chat = await self._get_chat(chat_id, with_members=True)
        # if not await self.chat_repo.is_member(self.session, chat_id, current_user_id):
        if current_user_id not in [member.user.id for member in chat.members]:
            raise ForbiddenError(
                "У вас нет прав на добавление участника в чат " + str(chat_id)
            )
        invite_token = create_jwt_token(
            {"sub": str(chat.id), "iss": current_user_id},
            token_type=TokenType.CHAT_INVITE_LINK,
        )
        return invite_token, chat.name

    async def add_member_to_chat_by_invite_token(
        self, token: str, current_user_id: int
    ) -> tuple[Chat, str]:
        token_data = validate_token(token, token_type=TokenType.CHAT_INVITE_LINK)
        chat = await self._get_chat(token_data.sub, with_members=True)
        invited_user = await self._get_user(token_data.iss)
        if current_user_id in [member.user.id for member in chat.members]:
            message = f"Вы уже были добавлены в чат {chat.name}"
            raise AlreadyMemberChatError(message)
        await self.chat_repo.add_member(
            self.session, chat.id, current_user_id, invited_user.id
        )
        await self.session.commit()
        return chat, invited_user.username

    async def is_member(self, chat_id: uuid.UUID, current_user_id: int) -> bool:
        if not await self.chat_repo.is_member(self.session, chat_id, current_user_id):
            raise ForbiddenError(
                "У вас нет прав на получение сообщений в чате " + str(chat_id)
            )
        return True
