import uuid

import pytest
from domains.auth.security import decrypt_message
from domains.chats.models import Chat
from domains.messages.models import Message
from domains.users.models import User
from fastapi import status
from faststream.kafka import TestKafkaBroker
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.message
async def test_send_message(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
    test_chat: Chat,
    test_user: User,
    kafka_broker: TestKafkaBroker,
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
    assert decrypt_message(message.text) == message_body


@pytest.mark.message
async def test_send_message_in_non_existing_chat(
    client: AsyncClient,
    session: AsyncSession,
    access_token: str,
) -> None:
    random_chat = uuid.uuid4()
    message_body = "Hi, everyone!"
    response = await client.post(
        "/messages/",
        json={"text": message_body, "chat_id": str(random_chat)},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(random_chat) in response.json()["message"]


@pytest.mark.message
async def test_send_message_without_permission(
    client: AsyncClient,
    session: AsyncSession,
    member_access_token: str,
    test_chat: Chat,
) -> None:
    message_body = "Hi, everyone!"
    response = await client.post(
        "/messages/",
        json={"text": message_body, "chat_id": str(test_chat.id)},
        headers={"Authorization": f"Bearer {member_access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    result = await session.scalar(
        select(func.count(Message.id)).where(Message.chat_id == test_chat.id)
    )
    assert result == 0
