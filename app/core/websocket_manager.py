from dataclasses import dataclass
from functools import cache
from uuid import UUID

from domains.chats.broker import ChatBroker
from domains.chats.schemas import ChatEvent, WebsocketEvent
from fastapi import WebSocket


@dataclass(frozen=True, slots=True)
class ChatConnection:
    websocket: WebSocket
    user_id: int


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self.chat_connections: dict[UUID, list[ChatConnection]] = {}

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

    def disconnect_from_chat(self, websocket: WebSocket, chat_id: UUID) -> None:
        if chat_id in self.chat_connections:
            self.chat_connections[chat_id] = [
                connection
                for connection in self.chat_connections[chat_id]
                if connection.websocket != websocket
            ]

    async def close_connection(
        self, chat_id: UUID, user_id: int, websocket: WebSocket, broker: ChatBroker
    ) -> None:
        self.disconnect_from_chat(websocket, chat_id)
        await broker.remove_user(user_id, chat_id)
        await self.chat_broadcast(
            WebsocketEvent(
                event=ChatEvent.disconnect_user,
                payload=user_id,
            ),
            chat_id,
            broker,
        )
        await websocket.close()

    async def close_all_user_connections(
        self, user_id: int, broker: ChatBroker
    ) -> None:
        for chat_id in self.chat_connections:
            user_connections = [
                connection
                for connection in self.chat_connections[chat_id]
                if connection.user_id == user_id
            ]
            for connection in user_connections:
                await self.close_connection(
                    chat_id, connection.user_id, connection.websocket, broker
                )

    async def remove_from_chat_by_user_id(self, user_id: int, chat_id: UUID) -> None:
        if chat_id in self.chat_connections:
            user_connections = [
                connection
                for connection in self.chat_connections[chat_id]
                if connection.user_id == user_id
            ]
            for connection in user_connections:
                await connection.websocket.close()
                self.chat_connections[chat_id].remove(connection)

    # async def send_personal_message(self, message: str, websocket: WebSocket):
    #     await websocket.send_text(message)

    async def chat_broadcast(
        self,
        data: WebsocketEvent,
        chat_id: UUID,
        broker: ChatBroker,
        is_published: bool = False,
    ) -> None:
        if not is_published:
            await broker.publish_event(chat_id, data)
        elif chat_id in self.chat_connections:
            for connection in self.chat_connections[chat_id]:
                await connection.websocket.send_json(data.model_dump(mode="json"))

    async def dispose(self) -> None:
        for chat_connection in self.chat_connections.values():
            for connection in chat_connection:
                await connection.websocket.close()
        self.chat_connections.clear()


@cache
def get_websocket_manager() -> WebSocketConnectionManager:
    return WebSocketConnectionManager()
