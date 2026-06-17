import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import jwt
from core.config import settings
from pwdlib import PasswordHash
from pydantic import ValidationError

from domains.auth.errors import UnauthorizedError
from domains.auth.schemas import JWTPayload, TokenData, TokenType

password_hash = PasswordHash.recommended()


@lru_cache(maxsize=1)
def get_dummy_hash() -> str:
    return password_hash.hash("dummypassword")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_jwt_token(
    data: dict[str, Any],
    expires_minutes: int = settings.security.expires_minutes,
    token_type: TokenType = TokenType.ACCESS,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=UTC) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "type": token_type})
    to_encode = JWTPayload(**to_encode).model_dump(exclude_unset=True)
    return jwt.encode(
        to_encode, settings.security.secret_key, algorithm=settings.security.algorithm
    )


def validate_token(token: str, token_type: TokenType = TokenType.ACCESS) -> TokenData:
    try:
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
        )
        if not payload.get("type") == token_type:
            raise UnauthorizedError
        sub = payload.get("sub")
        iss = payload.get("iss")
        if sub is None:
            raise UnauthorizedError
        return TokenData(sub=sub, iss=iss)
    except (jwt.InvalidTokenError, ValidationError, ValueError) as exc:
        raise UnauthorizedError from exc
