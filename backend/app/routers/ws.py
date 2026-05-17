from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket_manager import websocket_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/progress/{job_id}")
async def progress_ws(websocket: WebSocket, job_id: UUID) -> None:
    await websocket_manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(job_id, websocket)
