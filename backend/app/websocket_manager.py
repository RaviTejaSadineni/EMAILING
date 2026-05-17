from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, job_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[job_id].add(websocket)

    def disconnect(self, job_id: UUID, websocket: WebSocket) -> None:
        self.active_connections[job_id].discard(websocket)
        if not self.active_connections[job_id]:
            self.active_connections.pop(job_id, None)

    async def broadcast(self, job_id: UUID, message: str) -> None:
        for connection in tuple(self.active_connections.get(job_id, ())):
            await connection.send_text(message)


websocket_manager = WebSocketManager()
