import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.chat
async def test_create_chat(
    client: AsyncClient, session: AsyncSession, access_token: str
) -> None:
    chat_name = "Test Chat"
    response = await client.post(
        "/chats/",
        json={"name": chat_name},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert chat_name in response.json()["message"]
    assert response.json()["details"]["chat_id"]
