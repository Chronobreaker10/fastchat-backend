from core.base.errors import BaseHTTPError
from fastapi import status


class ChatNotFoundError(BaseHTTPError):
    code: int = status.HTTP_404_NOT_FOUND
    message: str = "Чат не найден"


class AlreadyMemberChatError(BaseHTTPError):
    code: int = status.HTTP_409_CONFLICT
    message: str = "Пользователь уже добавлен в чат"


class AlreadyNotMemberChatError(BaseHTTPError):
    code: int = status.HTTP_404_NOT_FOUND
    message: str = "Пользователя нет в этом чате"
