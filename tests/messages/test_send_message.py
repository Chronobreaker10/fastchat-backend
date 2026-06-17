import pytest
from domains.chats.models import Chat
from domains.messages.models import Message
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.message
async def test_send_message(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    test_chat: Chat,
    test_user: User,
) -> None:
    message_body = "Hi, everyone!"
    response = await client.post(
        "/messages/",
        json={"text": message_body, "chat_id": str(test_chat.id)},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()["details"]["message"]
    assert str(test_chat.id) == data["chat_id"]
    assert test_user.id == data["sender_id"]
    assert message_body == data["text"]
    assert data["id"]
    message = await session.scalar(select(Message).where(Message.id == data["id"]))
    assert message.text == message_body
