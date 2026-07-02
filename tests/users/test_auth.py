import pytest
from core.config import settings
from domains.auth.security import hash_token
from domains.auth.session_store import SessionStore
from domains.users.models import User
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.auth
async def test_register_user(
    client: AsyncClient,
    sessions_store: SessionStore,
) -> None:
    username = "test_register"
    password = "test_pass"
    response = await client.post(
        "/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]
    assert response.json()["token_type"] == "Bearer"
    refresh_token_hash = hash_token(response.json()["refresh_token"])
    user_session = await sessions_store.get_session(refresh_token_hash)
    assert user_session is not None


@pytest.mark.auth
async def test_login_user(
    client: AsyncClient, test_user: User, sessions_store: SessionStore
) -> None:
    response = await client.post(
        "/auth/token", data={"username": "test_user", "password": "secret"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]
    assert response.json()["token_type"] == "Bearer"
    refresh_token_hash = hash_token(response.json()["refresh_token"])
    user_session = await sessions_store.get_session(refresh_token_hash)
    assert user_session is not None
    assert user_session.user_id == test_user.id


@pytest.mark.auth
@pytest.mark.parametrize(
    "username, password, status_code",
    [
        ("", "", status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("test_user", "111", status.HTTP_401_UNAUTHORIZED),
        ("user_test", "111", status.HTTP_401_UNAUTHORIZED),
        ("user_test", "secret", status.HTTP_401_UNAUTHORIZED),
    ],
)
async def test_unsuccessful_login_user(
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
    response = await client.get("/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "test_user"


@pytest.mark.auth
async def test_logout_user(
    client: AsyncClient,
    test_user: User,
    access_token: str,
    sessions_store: SessionStore,
) -> None:
    assert client.cookies.get(settings.security.access_token_cookie_name) is not None
    assert client.cookies.get(settings.security.refresh_token_cookie_name) is not None
    refresh_token_hash = await sessions_store.get_refresh_token(test_user.id)
    assert refresh_token_hash is not None
    user_session = await sessions_store.get_session(refresh_token_hash)
    assert user_session is not None
    assert user_session.user_id == test_user.id
    response = await client.delete("/auth/logout")
    assert response.status_code == status.HTTP_200_OK
    assert client.cookies.get(settings.security.access_token_cookie_name) is None
    assert client.cookies.get(settings.security.refresh_token_cookie_name) is None
    user_session = await sessions_store.get_session(refresh_token_hash)
    assert user_session is None
    refresh_token_hash = await sessions_store.get_refresh_token(test_user.id)
    assert refresh_token_hash is None
