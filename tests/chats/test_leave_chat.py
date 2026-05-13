import uuid

import pytest
from domains.chats.models import Chat, ChatUser
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.chat
async def test_leave_chat(
    client: AsyncClient,
    session: AsyncSession,
    chat_member: User,
    member_access_token: str,
    test_chat: Chat,
) -> None:
    response = await client.delete(
        f"/chats/{test_chat.id}/members",
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_chat.name in response.json()["message"]
    assert str(test_chat.id) == response.json()["details"]["chat_id"]
    result = await session.scalar(
        select(func.count(ChatUser.id)).where(
            ChatUser.chat_id == test_chat.id, ChatUser.user_id == chat_member.id
        )
    )
    assert result == 0


@pytest.mark.chat
async def test_not_member_leave_chat(
    client: AsyncClient,
    session: AsyncSession,
    member: User,
    member_access_token: str,
    test_chat: Chat,
) -> None:
    response = await client.delete(
        f"/chats/{test_chat.id}/members",
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert test_chat.name in response.json()["message"]


@pytest.mark.chat
async def test_leave_non_existing_chat(
    client: AsyncClient, session: AsyncSession, member: User, member_access_token: str
) -> None:
    random_chat = uuid.uuid4()
    response = await client.delete(
        f"/chats/{random_chat}/members",
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(random_chat) in response.json()["message"]


@pytest.mark.chat
async def test_leave_chat_owner(
    client: AsyncClient,
    session: AsyncSession,
    test_user: User,
    access_token: str,
    test_chat: Chat,
) -> None:
    response = await client.delete(
        f"/chats/{test_chat.id}/members",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_chat.name in response.json()["message"]
    assert str(test_chat.id) == response.json()["details"]["chat_id"]
    result = await session.scalar(
        select(func.count(Chat.id)).where(Chat.id == test_chat.id)
    )
    assert result == 0
