from core.base.errors import BaseHTTPError
from fastapi import status


class UserNotFoundError(BaseHTTPError):
    code: int = status.HTTP_404_NOT_FOUND
    message: str = "Пользователь не найден"


class UserAlreadyExistsError(BaseHTTPError):
    code: int = status.HTTP_409_CONFLICT
    message: str = "Пользователь с таким именем уже существует"
