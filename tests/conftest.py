from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import Mock

import pytest
from core.base.models import Base
from core.config import settings
from core.database import db_helper
from core.websocket_manager import ConnectionManager, get_websocket_manager
from domains.auth.security import get_password_hash
from domains.chats.broker import ChatBroker
from domains.chats.dependencies import get_chat_broker
from domains.chats.models import Chat, ChatUser
from domains.users.models import User
from httpx import ASGITransport, AsyncClient
from main import app
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_factory = async_sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False
)


@pytest.fixture
def mock_chat_broker() -> Mock:
    # Создаём мок-объект с нужным методом
    mock_broker = Mock(spec=ChatBroker)
    mock_broker.get_online_users.return_value = [1]
    return mock_broker


@pytest.fixture(autouse=True, scope="function")
async def setup_database() -> AsyncGenerator[None]:
    """Создает и очищает БД для каждого теста"""
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="session")
async def get_session_override() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest.fixture(name="client")
async def test_client(
    session: AsyncSession, mock_chat_broker: Mock
) -> AsyncGenerator[AsyncClient, Any]:
    async def get_override_session() -> AsyncSession:
        return session

    async def get_override_websocket_manager() -> ConnectionManager:
        return ConnectionManager()

    app.dependency_overrides[db_helper.get_session] = get_override_session
    app.dependency_overrides[get_websocket_manager] = get_override_websocket_manager
    app.dependency_overrides[get_chat_broker] = lambda: mock_chat_broker
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f"http://testhost{settings.api_config.prefix}",
    ) as client:
        yield client
    app.dependency_overrides.clear()


@asynccontextmanager
async def _create_user(
    username: str, password: str, session: AsyncSession
) -> AsyncGenerator[User, Any]:
    password = get_password_hash(password)
    test_user = User(username=username, hashed_password=password)
    session.add(test_user)
    await session.flush()
    # await session.commit()
    try:
        yield test_user
    finally:
        await session.rollback()
        # await session.delete(test_user)
        # await session.commit()


@pytest.fixture(scope="function", name="test_user")
async def create_test_user(
    session: AsyncSession, setup_database: None
) -> AsyncGenerator[User, Any]:
    async with _create_user("test_user", "secret", session) as user:
        yield user


@pytest.fixture(scope="function", name="member")
async def create_test_member(
    session: AsyncSession, setup_database: None
) -> AsyncGenerator[User, Any]:
    async with _create_user("member", "secret", session) as user:
        yield user


@pytest.fixture(name="access_token")
async def login_user(client: AsyncClient, test_user: User) -> str:
    response = await client.post(
        "/auth/token", data={"username": "test_user", "password": "secret"}
    )
    return response.json()["access_token"]


@pytest.fixture(name="member_access_token")
async def login_member(client: AsyncClient, member: User) -> str:
    response = await client.post(
        "/auth/token", data={"username": "member", "password": "secret"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function", name="test_chat")
async def create_test_chat(
    session: AsyncSession, setup_database: None, test_user: User
) -> AsyncGenerator[Chat, Any]:
    test_chat = Chat(name="test_chat", user_id=test_user.id)
    session.add(test_chat)
    await session.flush()
    chat_user = ChatUser(chat_id=test_chat.id, user_id=test_user.id)
    session.add(chat_user)
    await session.flush()
    try:
        yield test_chat
    finally:
        await session.rollback()
