import uuid

import pytest
from domains.chats.models import Chat
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.chat
async def test_delete_chat(
    client: AsyncClient, session: AsyncSession, access_token: str, test_chat: Chat
) -> None:
    response = await client.delete(
        f"/chats/{test_chat.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_chat.name in response.json()["message"]
    assert response.json()["details"]["chat_id"]
    result = await session.scalar(
        select(func.count(Chat.id)).where(Chat.id == test_chat.id)
    )
    assert result == 0


@pytest.mark.chat
async def test_delete_non_existing_chat(
    client: AsyncClient, session: AsyncSession, access_token: str
) -> None:
    random_chat = uuid.uuid4()
    response = await client.delete(
        f"/chats/{random_chat}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(random_chat) in response.json()["message"]


@pytest.mark.chat
async def test_delete_chat_without_permission(
    client: AsyncClient,
    session: AsyncSession,
    member_access_token: str,
    test_chat: Chat,
) -> None:
    response = await client.delete(
        f"/chats/{test_chat.id}",
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(test_chat.id) in response.json()["message"]
    result = await session.scalar(
        select(func.count(Chat.id)).where(Chat.id == test_chat.id)
    )
    assert result == 1
