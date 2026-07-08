import pytest
from domains.auth.security import decrypt_message
from domains.messages.models import Message
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.message
async def test_update_message(
    client: AsyncClient, session: AsyncSession, access_token: str, test_message: Message
) -> None:
    new_text = "test2"
    response = await client.patch(
        f"/messages/{test_message.id}",
        json={"text": new_text},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_message.id == response.json()["details"]["message"]["id"]
    result = await session.execute(
        select(Message.text).where(Message.id == test_message.id)
    )
    assert (
        response.json()["details"]["message"]["text"]
        == new_text
        == decrypt_message(result.mappings().one()["text"])
    )


@pytest.mark.message
async def test_update_message_without_permission(
    client: AsyncClient,
    session: AsyncSession,
    member_access_token: str,
    test_message: Message,
) -> None:
    new_text = "test2"
    response = await client.patch(
        f"/messages/{test_message.id}",
        json={"text": new_text},
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(test_message.id) in response.json()["message"]
    result = await session.execute(
        select(Message.text).where(Message.id == test_message.id)
    )
    assert result.mappings().one()["text"] == test_message.text


@pytest.mark.chat
async def test_update_non_existing_message(
    client: AsyncClient, session: AsyncSession, access_token: str, test_message: Message
) -> None:
    message_id = 12345
    new_text = "test2"
    response = await client.patch(
        f"/messages/{message_id}",
        json={"text": new_text},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(message_id) in response.json()["message"]
