from typing import Callable, Dict, List
from app.api.v1.websocket import manager  # reuse WebSocket manager for broadcast

subscribers: Dict[str, List[Callable]] = {}

def subscribe(event_name: str, handler: Callable):
    if event_name not in subscribers:
        subscribers[event_name] = []
    subscribers[event_name].append(handler)

def emit(event_name: str, payload: dict):
    handlers = subscribers.get(event_name, [])
    for handler in handlers:
        handler(payload)

    # Also push directly to WebSocket
    import asyncio
    asyncio.create_task(manager.broadcast(f"{event_name}: {payload}"))