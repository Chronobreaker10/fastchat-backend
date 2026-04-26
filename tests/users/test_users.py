from domains.users.models import User
from fastapi import status
from httpx import AsyncClient


async def test_get_user_by_username(client: AsyncClient, test_user: User) -> None:
    test_username = "test_user"
    response = await client.get(f"/users/{test_username}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_username


async def test_get_not_exists_user(client: AsyncClient, test_user: User) -> None:
    test_username = "not_exists_user"
    response = await client.get(f"/users/{test_username}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"message": "Пользователь не найден"}
