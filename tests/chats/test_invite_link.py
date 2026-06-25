import uuid

import pytest
from domains.auth.schemas import TokenType
from domains.auth.security import create_jwt_token
from domains.chats.models import Chat
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.chat
async def test_generate_invite_link(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    test_chat: Chat,
) -> None:
    response = await client.get(
        f"/chats/{test_chat.id}/invite",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_chat.name in response.json()["chat_name"]


@pytest.mark.chat
async def test_generate_non_existing_chat_invite_link(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
) -> None:
    random_chat = uuid.uuid4()
    response = await client.get(
        f"/chats/{random_chat}/invite",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(random_chat) in response.json()["message"]


@pytest.mark.chat
async def test_generate_invite_link_without_permission(
    client: AsyncClient,
    session: AsyncSession,
    member_access_token: str,
    test_chat: Chat,
) -> None:
    response = await client.get(
        f"/chats/{test_chat.id}/invite",
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(test_chat.id) in response.json()["message"]


@pytest.mark.chat
async def test_join_by_non_existing_chat_invite_link(
    client: AsyncClient,
    session: AsyncSession,
    member_access_token: str,
    member: User,
    test_user: User,
) -> None:
    random_chat = uuid.uuid4()
    token = create_jwt_token(
        {"sub": str(random_chat), "iss": test_user.id},
        token_type=TokenType.CHAT_INVITE_LINK,
    )
    response = await client.post(
        "/chats/invite",
        json={"invite_token": token},
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(random_chat) in response.json()["message"]


@pytest.mark.chat
async def test_join_already_member_by_invite_link(
    client: AsyncClient,
    session: AsyncSession,
    chat_member: User,
    member_access_token: str,
    invite_link: str,
    test_chat: Chat,
) -> None:
    response = await client.post(
        "/chats/invite",
        json={"invite_token": invite_link},
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert test_chat.name in response.json()["message"]


@pytest.mark.chat
async def test_join_by_invite_link(
    client: AsyncClient,
    session: AsyncSession,
    member_access_token: str,
    member: User,
    test_user: User,
    invite_link: str,
    test_chat: Chat,
) -> None:
    client.cookies.clear()
    response = await client.post(
        "/chats/invite",
        json={"invite_token": invite_link},
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_chat.name in response.json()["message"]
    assert test_user.username in response.json()["message"]
    assert member.username in response.json()["message"]
    assert str(test_chat.id) == response.json()["details"]["chat_id"]
