import pytest
from domains.auth.security import decrypt_message
from domains.chats.models import Chat
from domains.messages.models import Message, MessageStatus
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient


@pytest.mark.chat
async def test_get_messages(
    client: AsyncClient,
    access_token: str,
    test_chat: Chat,
    test_user: User,
    test_messages: list[Message],
) -> None:
    limit = 3
    for message in test_messages:
        assert message.message_status == MessageStatus.DELIVERED
    response = await client.get(
        f"/chats/{test_chat.id}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "limit": limit,
            "date": test_messages[0].created_at.isoformat(),
            "entity_id": test_messages[0].id,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    messages = response.json()
    assert len(messages) == limit
    for i in range(1, limit + 1):
        assert messages[-i]["id"] == test_messages[i].id
        assert messages[-i]["text"] == decrypt_message(test_messages[i].text)
        assert messages[-i]["chat_id"] == str(test_chat.id)
        assert messages[-i]["sender_id"] == test_user.id
        assert messages[-i]["sender"]["username"] == test_user.username
        assert messages[-i]["message_status"] == MessageStatus.DELIVERED


@pytest.mark.chat
async def test_member_get_messages(
    client: AsyncClient,
    member_access_token: str,
    test_chat: Chat,
    chat_member: User,
    test_messages: list[Message],
) -> None:
    limit = 3
    for message in test_messages:
        assert message.message_status == MessageStatus.DELIVERED
    response = await client.get(
        f"/chats/{test_chat.id}/messages",
        headers={"Authorization": f"Bearer {member_access_token}"},
        params={
            "limit": limit,
            "date": test_messages[0].created_at.isoformat(),
            "entity_id": test_messages[0].id,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    messages = response.json()
    assert len(messages) == limit
    for i in range(1, limit + 1):
        assert messages[-i]["message_status"] == MessageStatus.READ
