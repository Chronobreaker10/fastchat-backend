from core.base.errors import BaseHTTPError
from fastapi import status


class UnauthorizedError(BaseHTTPError):
    code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "Для доступа к ресурсу необходимо авторизоваться"

    def __init__(self) -> None:
        self.headers = {"WWW-Authenticate": "Bearer"}


class InvalidCredentialsError(BaseHTTPError):
    code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "Проверьте имя и пароль"

    def __init__(self) -> None:
        self.headers = {"WWW-Authenticate": "Bearer"}


class InvalidIPAddressError(BaseHTTPError):
    code: int = status.HTTP_422_UNPROCESSABLE_CONTENT
    message: str = "Некорректный IP адрес"


class ForbiddenError(BaseHTTPError):
    code: int = status.HTTP_403_FORBIDDEN
    message: str = "У вас недостаточно прав для выполнения этого действия"
