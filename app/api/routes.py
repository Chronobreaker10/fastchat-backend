from domains.auth.router import router as auth_router
from domains.chats.router import router as chat_router
from domains.users.router import router as users_router
from fastapi import FastAPI


def setup_routes(app: FastAPI) -> None:
    app.include_router(users_router)
    app.include_router(auth_router)
    app.include_router(chat_router)
