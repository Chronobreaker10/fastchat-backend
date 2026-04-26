from collections.abc import AsyncGenerator
from typing import Any

import pytest
from core.base.models import Base
from core.database import db_helper
from httpx import ASGITransport, AsyncClient
from main import app
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_factory = async_sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False
)


@pytest.fixture(autouse=True, scope="session")
async def setup_database() -> None:
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(name="session", scope="session")
async def get_session_override() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest.fixture(name="client", scope="session")
async def test_client(session: AsyncSession) -> AsyncGenerator[AsyncClient, Any]:
    async def get_override_session() -> AsyncSession:
        return session

    app.dependency_overrides[db_helper.get_session] = get_override_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testhost"
    ) as client:
        yield client
    app.dependency_overrides.clear()
