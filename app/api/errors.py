from core.base.errors import BaseHTTPError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


async def handle_base_http_error(_: Request, exc: BaseHTTPError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code,
        content={"message": exc.message},
        headers=getattr(exc, "headers", None),
    )


def setup_exceptions(app: FastAPI) -> None:
    app.add_exception_handler(BaseHTTPError, handle_base_http_error)
