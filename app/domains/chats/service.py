import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from domains.chats.errors import AlreadyMemberChatError, ChatNotFoundError
from domains.chats.models import Chat
from domains.chats.repository import ChatRepository
from domains.chats.schemas import ChatCreate, ChatCreateInDB, ChatRead
from domains.users.errors import UserNotFoundError
from domains.users.repository import UserRepository


class ChatService:
    def __init__(
        self,
        chat_repo: ChatRepository,
        user_repo: UserRepository,
        session: AsyncSession,
    ) -> None:
        self.chat_repo = chat_repo
        self.user_repo = user_repo
        self.session = session

    async def add_member_to_chat(self, chat_id: uuid.UUID, user_id: int) -> None:
        user = await self.user_repo.get_by_id(self.session, user_id)
        if user is None:
            raise UserNotFoundError
        chat = await self.chat_repo.get_by_uuid(self.session, chat_id)
        if chat is None:
            raise ChatNotFoundError
        if await self.chat_repo.is_member(self.session, chat_id, user_id):
            raise AlreadyMemberChatError
        await self.chat_repo.add_member(self.session, chat_id, user_id)

    async def create_chat(self, creator_id: int, data: ChatCreate) -> Chat:
        chat_data = ChatCreateInDB(user_id=creator_id, **data.model_dump())
        chat = await self.chat_repo.create(self.session, chat_data)
        await self.add_member_to_chat(chat.id, creator_id)
        await self.session.commit()
        return chat

    async def get_user_chats(self, user_id: int) -> list[ChatRead]:
        chats = await self.chat_repo.get_chats_by_user_id(self.session, user_id)
        return [ChatRead.model_validate(chat) for chat in chats]
