from datetime import UTC, datetime, timedelta

import jwt
from domains.auth.errors import UnauthorizedError
from pwdlib import PasswordHash

from core.base.schemas import TokenData
from core.config import settings

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(
    data: dict, expires_minutes: int = settings.security.expires_minutes
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.security.secret_key, algorithm=settings.security.algorithm
    )


def validate_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError
        return TokenData(user_id=user_id)
    except jwt.InvalidTokenError:
        raise UnauthorizedError
