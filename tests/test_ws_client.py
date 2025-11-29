import asyncio
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    logger.info(f"Attempting to connect to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected successfully!")
            
            await websocket.send("Hello from Python client")
            logger.info("Sent message")
            
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"❌ WebSocket error: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
