import pytest
from domains.chats.models import Chat
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient


@pytest.mark.chat
async def test_get_my_chats(
    client: AsyncClient, access_token: str, test_chat: Chat, test_user: User
) -> None:
    response = await client.get(
        "/chats/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    chats = response.json()
    assert len(chats) == 1
    assert chats[0]["name"] == test_chat.name
    assert chats[0]["creator"]["id"] == test_user.id
    assert chats[0]["members"][0]["user"]["id"] == test_user.id
