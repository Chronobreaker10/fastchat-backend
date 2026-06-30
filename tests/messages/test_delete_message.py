import pytest
from domains.messages.models import Message
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.message
async def test_delete_message(
    client: AsyncClient, session: AsyncSession, access_token: str, test_message: Message
) -> None:
    response = await client.delete(
        f"/messages/{test_message.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert test_message.id == response.json()["details"]["message_id"]
    result = await session.scalar(
        select(func.count(Message.id)).where(Message.id == test_message.id)
    )
    assert result == 0
