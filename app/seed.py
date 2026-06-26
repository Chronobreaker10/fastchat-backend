import asyncio
from datetime import datetime, timedelta
from random import choice, randint, sample
from uuid import UUID

from core.database import db_helper
from domains.auth.service import AuthService
from domains.chats.repository import ChatRepository
from domains.chats.schemas import ChatCreate
from domains.chats.service import ChatService
from domains.messages.repository import MessageRepository
from domains.messages.schemas import MessageCreate
from domains.users.repository import UserRepository
from domains.users.schemas import UserCreate
from faker import Faker
from pydantic import create_model

fake = Faker("ru_RU")

users = set()
chats = []
messages = set()


async def create_users(count: int = 10) -> None:
    async with db_helper.session_factory() as session:
        service = AuthService(UserRepository(), session)
        for i in range(count):
            username = fake.user_name()
            password = str(i) * 5
            await service.register_user(
                UserCreate(username=username, password=password)
            )
            users.add(username)


async def create_chats(count: int = 5, members_count: int = 3) -> None:
    async with db_helper.session_factory() as session:
        user_repo = UserRepository()
        chat_repo = ChatRepository()
        service = ChatService(chat_repo, UserRepository(), MessageRepository(), session)
        for _i in range(count):
            creator = await user_repo.get_by_username(session, choice(list(users)))  # noqa: S311
            if creator is not None:
                chat_name = fake.sentence(
                    nb_words=randint(3, 6),  # noqa: S311
                    variable_nb_words=True,
                )[:-1].capitalize()
                chat = await service.create_chat(creator.id, ChatCreate(name=chat_name))
                members = sample(
                    list(users.difference({creator.username})), k=members_count
                )
                for member in members:
                    user = await user_repo.get_by_username(session, member)
                    if user is not None:
                        await chat_repo.add_member(
                            session, chat.id, user.id, creator.id
                        )
                await session.commit()
                chats.append({"chat": chat, "members": members})


async def create_messages(count: int = 100) -> None:
    message_create_fake = create_model(
        "MessageCreateFake",
        text=(str, ...),
        chat_id=(UUID, ...),
        sender_id=(int, ...),
        created_at=(datetime, ...),
    )
    async with db_helper.session_factory() as session:
        message_repo = MessageRepository()
        user_repo = UserRepository()
        for _i in range(count):
            chat = choice(chats)  # noqa S311
            chat_obj = chat["chat"]
            members = chat["members"]
            sender = await user_repo.get_by_username(session, choice(members))  # noqa: S311
            if sender is not None:
                data = MessageCreate(
                    text=fake.sentence(nb_words=randint(3, 10), variable_nb_words=True),  # noqa: S311
                    chat_id=chat_obj.id,
                )
                data = message_create_fake(
                    **data.model_dump(),
                    sender_id=sender.id,
                    created_at=datetime.now(tz=None)
                    - timedelta(minutes=randint(1, 100)),  # noqa: S311
                )
                message = await message_repo.create(session, data)
                messages.add(message)
                await session.commit()


async def main() -> None:
    await create_users(count=10)
    await create_chats(count=4)
    await create_messages(count=100)


if __name__ == "__main__":
    asyncio.run(main())
