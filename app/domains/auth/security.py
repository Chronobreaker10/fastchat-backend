from datetime import datetime, timedelta

import jwt
from core.config import settings
from pwdlib import PasswordHash

from domains.auth.errors import UnauthorizedError
from domains.auth.schemas import JWTTokenPayload, TokenData, TokenType

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_jwt_token(
    data: dict,
    expires_minutes: int = settings.security.expires_minutes,
    token_type: TokenType = TokenType.ACCESS,
) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "type": token_type})
    to_encode = JWTTokenPayload(**to_encode).model_dump(exclude_unset=True)
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
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError
        return TokenData(user_id=user_id)
    except jwt.InvalidTokenError:
        raise UnauthorizedError
