import random
import string
import uuid

import pytest
from domains.chats.models import Chat, ChatUser
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.chat
async def test_add_member(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    member: User,
    test_chat: Chat,
) -> None:
    response = await client.post(
        f"/chats/{test_chat.id}/members",
        json=member.username,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_chat.name in response.json()["message"]
    assert member.username in response.json()["message"]
    assert str(test_chat.id) == response.json()["details"]["chat_id"]
    result = await session.scalar(
        select(func.count(ChatUser.id)).where(
            ChatUser.chat_id == test_chat.id, ChatUser.user_id == member.id
        )
    )
    assert result == 1


@pytest.mark.chat
async def test_add_member_to_not_existing_chat(
    client: AsyncClient, session: AsyncSession, access_token: str, member: User
) -> None:
    random_chat = uuid.uuid4()
    response = await client.post(
        f"/chats/{random_chat}/members",
        json=member.username,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(random_chat) in response.json()["message"]


@pytest.mark.chat
async def test_add_not_existing_user(
    client: AsyncClient, session: AsyncSession, access_token: str, test_chat: Chat
) -> None:
    username = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    response = await client.post(
        f"/chats/{test_chat.id}/members",
        json=username,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert username in response.json()["message"]


@pytest.mark.chat
async def test_add_member_without_permission(
    client: AsyncClient,
    session: AsyncSession,
    member_access_token: str,
    test_chat: Chat,
    member: User,
) -> None:
    response = await client.post(
        f"/chats/{test_chat.id}/members",
        json=member.username,
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(test_chat.id) in response.json()["message"]


@pytest.mark.chat
async def test_add_already_member(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    test_chat: Chat,
    test_user: User,
) -> None:
    response = await client.post(
        f"/chats/{test_chat.id}/members",
        json=test_user.username,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert test_chat.name in response.json()["message"]
    assert test_user.username in response.json()["message"]
