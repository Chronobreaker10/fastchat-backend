from collections.abc import AsyncGenerator
from typing import Any

import pytest
from domains.users.models import User
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="function", name="test_user")
async def create_test_user(
    session: AsyncSession, setup_database: None
) -> AsyncGenerator[User, Any]:
    password = (
        "$argon2id$v=19$m=65536,"
        "t=3,p=4$SOZ/daFu2X+padPqO4+2xw$klOHJNuJuD8agwBksfT9qZ2VGvKdAY2OnLELFktXsL4"
    )
    test_user = User(username="test_user", hashed_password=password)
    session.add(test_user)
    await session.flush()
    try:
        yield test_user
    finally:
        await session.rollback()
