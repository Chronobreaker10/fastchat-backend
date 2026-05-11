import time
from collections.abc import Callable
from datetime import datetime

from core.logger import access_logger
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            process_time = time.perf_counter() - start_time
            timestamp = datetime.now().astimezone().strftime("%d/%b/%Y:%H:%M:%S %z")
            log_message = (
                f'{client_ip} - - [{timestamp}] "{request.method} {request.url.path} '
                f'HTTP/{request.scope.get("http_version", "1.1")}" '
                f'{status_code} - "-" "{request.headers.get("user-agent", "-")}" '
                f"{process_time:.3f}s"
            )
            access_logger.info(log_message)


def setup_middlewares(app: FastAPI) -> None:
    app.add_middleware(AccessLogMiddleware)
