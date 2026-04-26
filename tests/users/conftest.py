from collections.abc import AsyncGenerator
from typing import Any

import pytest
from domains.users.models import User
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="function")
async def create_test_user(
    session: AsyncSession, setup_database: None
) -> AsyncGenerator[None, Any]:
    password = "secret"
    test_user = User(username="test_user", hashed_password=password)
    session.add(test_user)
    await session.flush()
    try:
        yield
    finally:
        await session.rollback()
