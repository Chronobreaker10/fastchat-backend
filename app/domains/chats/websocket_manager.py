from dataclasses import dataclass
from functools import cache
from uuid import UUID

from core.config import settings
from core.redis import get_redis
from fastapi import WebSocket

from domains.chats.broker import ChatBroker
from domains.chats.schemas import ChatEvent, ClosedConnectionEvent, WebsocketEvent


@dataclass(frozen=True, slots=True)
class ChatConnection:
    websocket: WebSocket
    user_id: int


class ConnectionManager:
    def __init__(self) -> None:
        pass

    async def connect_to_chat(
        self, websocket: WebSocket, chat_id: UUID, user_id: int
    ) -> None:
        pass

    async def check_user_limit_connections(self, user_id: int) -> None:
        pass

    def disconnect_from_chat(self, websocket: WebSocket, chat_id: UUID) -> None:
        pass

    async def close_connection(
        self, chat_id: UUID, user_id: int, websocket: WebSocket, closed: bool = False
    ) -> None:
        pass

    async def close_user_connections_to_chat(
        self,
        chat_id: UUID,
        user_id: int,
        is_published: bool = False,
        is_removed: bool = False,
    ) -> None:
        pass

    async def chat_broadcast(
        self, data: WebsocketEvent, chat_id: UUID, is_published: bool = False
    ) -> None:
        pass

    async def dispose(self) -> None:
        pass


class WebSocketConnectionManager(ConnectionManager):
    def __init__(self) -> None:
        super().__init__()
        self.chat_connections: dict[UUID, list[ChatConnection]] = {}
        self.broker = ChatBroker(get_redis())

    async def connect_to_chat(
        self, websocket: WebSocket, chat_id: UUID, user_id: int
    ) -> None:
        await websocket.accept()
        if chat_id in self.chat_connections:
            self.chat_connections[chat_id].append(
                ChatConnection(websocket=websocket, user_id=user_id)
            )
        else:
            self.chat_connections[chat_id] = [
                ChatConnection(websocket=websocket, user_id=user_id)
            ]
        await self.broker.add_user(user_id, chat_id)
        await self.broker.add_connection(user_id, chat_id)
        await self.chat_broadcast(
            WebsocketEvent(
                event=ChatEvent.connect_user,
                payload=user_id,
            ),
            chat_id,
        )

    async def check_user_limit_connections(self, user_id: int) -> None:
        count_connections = await self.broker.get_count_user_connections(user_id)
        if count_connections >= settings.websockets_limit_per_user:
            connections = await self.broker.get_user_connections(
                user_id, -settings.websockets_limit_per_user
            )
            for connection in connections:
                await self.close_user_connections_to_chat(UUID(connection), user_id)
            await self.broker.remove_connections_by_rank(
                user_id,
                -settings.websockets_limit_per_user,
            )

    def disconnect_from_chat(self, websocket: WebSocket, chat_id: UUID) -> None:
        if chat_id in self.chat_connections:
            self.chat_connections[chat_id] = [
                connection
                for connection in self.chat_connections[chat_id]
                if connection.websocket != websocket
            ]

    async def close_connection(
        self, chat_id: UUID, user_id: int, websocket: WebSocket, closed: bool = False
    ) -> None:
        self.disconnect_from_chat(websocket, chat_id)
        await self.broker.remove_connection(user_id, chat_id)
        await self.broker.remove_user(user_id, chat_id)
        await self.chat_broadcast(
            WebsocketEvent(event=ChatEvent.disconnect_user, payload=user_id), chat_id
        )
        if not closed:
            await websocket.close()

    async def close_user_connections_to_chat(
        self,
        chat_id: UUID,
        user_id: int,
        is_published: bool = False,
        is_removed: bool = False,
    ) -> None:
        if not is_published:
            await self.broker.publish_closed_connection(
                ClosedConnectionEvent(
                    chat_id=chat_id, user_id=user_id, removed=is_removed
                )
            )
        if chat_id in self.chat_connections:
            user_connections = [
                connection
                for connection in self.chat_connections[chat_id]
                if connection.user_id == user_id
            ]
            for connection in user_connections:
                await self.close_connection(
                    chat_id, connection.user_id, connection.websocket
                )
                if is_removed and connection in self.chat_connections[chat_id]:
                    self.chat_connections[chat_id].remove(connection)

    # async def send_personal_message(self, message: str, websocket: WebSocket):
    #     await websocket.send_text(message)

    async def chat_broadcast(
        self, data: WebsocketEvent, chat_id: UUID, is_published: bool = False
    ) -> None:
        if not is_published:
            await self.broker.publish_chat_event(chat_id, data)
        elif chat_id in self.chat_connections:
            for connection in self.chat_connections[chat_id]:
                await connection.websocket.send_json(data.model_dump(mode="json"))

    async def dispose(self) -> None:
        for chat_connection in self.chat_connections.values():
            for connection in chat_connection:
                await connection.websocket.close()
        self.chat_connections.clear()


@cache
def get_websocket_manager() -> ConnectionManager:
    return WebSocketConnectionManager()
