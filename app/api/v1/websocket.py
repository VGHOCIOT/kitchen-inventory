from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    logger.info("=" * 50)
    logger.info("WebSocket connection attempt!")
    logger.info(f"Client: {websocket.client}")
    logger.info(f"Headers: {dict(websocket.headers)}")
    logger.info(f"Query params: {websocket.query_params}")
    logger.info(f"Path params: {websocket.path_params}")
    logger.info("=" * 50)
    
    try:
        await manager.connect(websocket)
        logger.info("✅ WebSocket connected successfully!")

        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message received: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {e}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {type(e).__name__}: {e}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)
        raise
