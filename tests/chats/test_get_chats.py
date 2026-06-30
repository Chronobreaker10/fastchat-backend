import pytest
from domains.auth.security import decrypt_message
from domains.chats.models import Chat
from domains.messages.models import Message
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient


@pytest.mark.chat
async def test_get_my_chats(
    client: AsyncClient,
    access_token: str,
    test_chat: Chat,
    test_user: User,
    test_messages: list[Message],
) -> None:
    response = await client.get(
        "/chats/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    chats = response.json()
    assert len(chats) == 1
    assert chats[0]["id"] == str(test_chat.id)
    assert chats[0]["name"] == test_chat.name
    assert chats[0]["last_message"]["chat_id"] == str(test_chat.id)
    assert chats[0]["last_message"]["id"] == test_messages[0].id
    assert chats[0]["last_message"]["text"] == decrypt_message(test_messages[0].text)


@pytest.mark.chat
async def test_get_chat(
    client: AsyncClient,
    access_token: str,
    test_chat: Chat,
    test_user: User,
    test_messages: list[Message],
    chat_member: User,
) -> None:
    count_members = 2
    response = await client.get(
        f"/chats/{test_chat.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    chat = response.json()
    assert chat["id"] == str(test_chat.id)
    assert chat["name"] == test_chat.name
    assert len(chat["members"]) == count_members
    assert len(chat["messages"]) == len(test_messages)
    for message in test_messages:
        assert len([item for item in chat["messages"] if item["id"] == message.id]) == 1
    assert (
        len([item for item in chat["members"] if item["user"]["id"] == test_user.id])
        == 1
    )
    assert (
        len([item for item in chat["members"] if item["user"]["id"] == chat_member.id])
        == 1
    )
