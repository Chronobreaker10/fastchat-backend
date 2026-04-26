from fastapi import status


class BaseHTTPError(Exception):
    code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Произошла непредвиденная ошибка"
    headers: dict | None = None

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
