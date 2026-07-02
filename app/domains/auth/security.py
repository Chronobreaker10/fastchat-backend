import hashlib
import secrets
from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import jwt
from core.config import settings
from cryptography.fernet import Fernet
from pwdlib import PasswordHash
from pydantic import ValidationError

from domains.auth.errors import UnauthorizedError
from domains.auth.schemas import JWTPayload, TokenData, TokenType

password_hash = PasswordHash.recommended()
encrypted_key = settings.security.encryption_key.encode()
key_hash = hashlib.sha256(encrypted_key).digest()
fernet = Fernet(urlsafe_b64encode(key_hash))


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


def encrypt_message(message: str) -> str:
    return fernet.encrypt(message.encode()).decode()


def decrypt_message(data: str) -> str:
    return fernet.decrypt(data.encode()).decode()


def create_jwt_token(
    data: dict[str, Any],
    expires_seconds: int = settings.security.access_token_expires_seconds,
    token_type: TokenType = TokenType.ACCESS,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=UTC) + timedelta(seconds=expires_seconds)
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
        username = payload.get("username")
        registered_at = payload.get("user_registered_at")
        if sub is None:
            raise UnauthorizedError
        return TokenData(
            sub=sub, iss=iss, username=username, user_registered_at=registered_at
        )
    except (jwt.InvalidTokenError, ValidationError, ValueError) as exc:
        raise UnauthorizedError from exc
