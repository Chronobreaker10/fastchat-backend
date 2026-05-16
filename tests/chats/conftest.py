from collections.abc import AsyncGenerator
from typing import Any

import pytest
from domains.chats.models import Chat, ChatUser
from domains.users.models import User
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="function", name="test_chat")
async def create_test_chat(
    session: AsyncSession, setup_database: None, test_user: User
) -> AsyncGenerator[Chat, Any]:
    test_chat = Chat(name="test_chat", user_id=test_user.id)
    session.add(test_chat)
    await session.flush()
    chat_user = ChatUser(chat_id=test_chat.id, user_id=test_user.id)
    session.add(chat_user)
    await session.flush()
    await session.commit()
    try:
        yield test_chat
    finally:
        await session.delete(chat_user)
        await session.delete(test_chat)
        await session.commit()


@pytest.fixture(scope="function", name="chat_member")
async def create_test_chat_member(
    session: AsyncSession, setup_database: None, test_chat: Chat, member: User
) -> AsyncGenerator[User, Any]:
    chat_user = ChatUser(chat_id=test_chat.id, user_id=member.id)
    session.add(chat_user)
    await session.flush()
    await session.commit()
    try:
        yield member
    finally:
        await session.flush()
        if chat_user:
            await session.delete(chat_user)
        await session.commit()


@pytest.fixture(scope="function", name="invite_link")
async def get_invite_link(
    client: AsyncClient, test_chat: Chat, access_token: str
) -> str:
    response = await client.get(
        f"/chats/{test_chat.id}/invite",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.json()["link"]
