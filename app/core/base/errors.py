from fastapi import status


class BaseHTTPError(Exception):
    code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Произошла непредвиденная ошибка"
    headers: dict | None = None

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message


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
