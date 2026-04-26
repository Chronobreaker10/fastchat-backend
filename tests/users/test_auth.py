import pytest
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.auth
async def test_register_user(client: AsyncClient, session: AsyncSession) -> None:
    username = "test_register"
    password = "test_pass"
    response = await client.post(
        "/auth/register",
        json={"user_data": {"username": username, "password": password}},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "Bearer"
    await session.execute(delete(User).where(User.username == username))
    await session.commit()


@pytest.mark.auth
@pytest.mark.parametrize(
    "username, password, status_code",
    [
        ("", "", status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("test_user", "111", status.HTTP_401_UNAUTHORIZED),
        ("user_test", "111", status.HTTP_401_UNAUTHORIZED),
        ("user_test", "secret", status.HTTP_401_UNAUTHORIZED),
        ("test_user", "secret", status.HTTP_200_OK),
    ],
)
async def test_login_user(
    client: AsyncClient, test_user: User, username: str, password: str, status_code: int
) -> None:
    response = await client.post(
        "/auth/token", data={"username": username, "password": password}
    )
    assert response.status_code == status_code


@pytest.mark.auth
async def test_get_unauthorized_profile(
    client: AsyncClient, session: AsyncSession
) -> None:
    response = await client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth
async def test_get_profile(client: AsyncClient, access_token: str) -> None:
    response = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "test_user"


@pytest.mark.auth
async def test_get_profile_by_cookie(client: AsyncClient, access_token: str) -> None:
    client.cookies.set("access_token", access_token)
    response = await client.get("/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "test_user"
    client.cookies.delete("access_token")
