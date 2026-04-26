from fastapi import status
from httpx import AsyncClient


async def test_get_user_by_username(
    client: AsyncClient, create_test_user: None
) -> None:
    test_username = "test_user"
    response = await client.get(f"/users/{test_username}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_username
    assert response.json()["id"] == 1


async def test_get_not_exists_user(client: AsyncClient, create_test_user: None) -> None:
    test_username = "not_exists_user"
    response = await client.get(f"/users/{test_username}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"message": "Пользователь не найден"}
