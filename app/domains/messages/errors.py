from core.base.errors import BaseHTTPError
from fastapi import status


class MessageNotFoundError(BaseHTTPError):
    code: int = status.HTTP_404_NOT_FOUND
    message: str = "Сообщение не найдено"
