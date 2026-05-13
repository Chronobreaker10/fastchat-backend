import uuid

import pytest
from domains.chats.models import Chat, ChatUser
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.chat
async def test_remove_member(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    chat_member: User,
    test_chat: Chat,
) -> None:
    response = await client.delete(
        f"/chats/{test_chat.id}/members/{chat_member.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_chat.name in response.json()["message"]
    assert chat_member.username in response.json()["message"]
    assert str(test_chat.id) == response.json()["details"]["chat_id"]
    result = await session.scalar(
        select(func.count(ChatUser.id)).where(
            ChatUser.chat_id == test_chat.id, ChatUser.user_id == chat_member.id
        )
    )
    assert result == 0


@pytest.mark.chat
async def test_remove_member_from_not_existing_chat(
    client: AsyncClient, session: AsyncSession, access_token: str, member: User
) -> None:
    random_chat = uuid.uuid4()
    response = await client.delete(
        f"/chats/{random_chat}/members/{member.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(random_chat) in response.json()["message"]


@pytest.mark.chat
async def test_remove_not_existing_user(
    client: AsyncClient, session: AsyncSession, access_token: str, test_chat: Chat
) -> None:
    user_id = 999_999
    response = await client.delete(
        f"/chats/{test_chat.id}/members/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(user_id) in response.json()["message"]


@pytest.mark.chat
async def test_remove_member_without_permission(
    client: AsyncClient,
    access_token: str,
    member_access_token: str,
    test_chat: Chat,
    chat_member: User,
) -> None:
    response = await client.delete(
        f"/chats/{test_chat.id}/members/{chat_member.id}",
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(test_chat.id) in response.json()["message"]


@pytest.mark.chat
async def test_remove_already_not_member(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    test_chat: Chat,
    member: User,
) -> None:
    response = await client.delete(
        f"/chats/{test_chat.id}/members/{member.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(member.id) in response.json()["message"]
    assert test_chat.name in response.json()["message"]
