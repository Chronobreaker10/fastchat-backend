import uuid

import pytest
from domains.chats.models import Chat
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.chat
@pytest.mark.parametrize(
    "data",
    [
        {
            "name": "Updated chat",
        },
        {
            "name": "Updated chat",
            "owner_id": 2,
        },
        {
            "owner_id": 2,
        },
    ],
)
async def test_update_chat(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    test_chat: Chat,
    data: dict,
    chat_member: User,
) -> None:
    response = await client.put(
        f"/chats/{test_chat.id}",
        json=data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["details"]["chat_id"]
    result = await session.execute(
        select(Chat.name, Chat.user_id).where(Chat.id == test_chat.id)
    )
    chat_from_db = result.mappings().one()
    assert chat_from_db["name"] == data.get("name", test_chat.name)
    assert chat_from_db["user_id"] == data.get("owner_id", test_chat.user_id)


@pytest.mark.chat
async def test_update_non_existing_chat(
    client: AsyncClient, session: AsyncSession, access_token: str, test_chat: Chat
) -> None:
    random_chat = uuid.uuid4()
    response = await client.put(
        f"/chats/{random_chat}",
        json={"name": "Updated chat"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(random_chat) in response.json()["message"]


@pytest.mark.chat
async def test_update_chat_without_permission(
    client: AsyncClient,
    session: AsyncSession,
    member_access_token: str,
    test_chat: Chat,
) -> None:
    response = await client.put(
        f"/chats/{test_chat.id}",
        json={"name": "Updated chat"},
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(test_chat.id) in response.json()["message"]
    result = await session.execute(select(Chat.name).where(Chat.id == test_chat.id))
    assert result.mappings().one()["name"] == test_chat.name


@pytest.mark.chat
async def test_update_chat_owner_not_member(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    test_chat: Chat,
    member: User,
) -> None:
    response = await client.put(
        f"/chats/{test_chat.id}",
        json={"owner_id": member.id},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(member.id) in response.json()["message"]
