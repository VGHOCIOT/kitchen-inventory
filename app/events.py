import asyncio
import logging
from typing import Callable, Dict, List

from api.v1.websocket import manager

logger = logging.getLogger(__name__)

subscribers: Dict[str, List[Callable]] = {}


def subscribe(event_name: str, handler: Callable):
    if event_name not in subscribers:
        subscribers[event_name] = []
    subscribers[event_name].append(handler)


def emit(event_name: str, payload: dict):
    """Emit an event to subscribers and broadcast via WebSocket.

    Payload must be a plain dict (JSON-serializable).
    """
    for handler in subscribers.get(event_name, []):
        handler(payload)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast_event(event_name, payload))
    except RuntimeError:
        logger.debug(f"No running event loop, skipping WebSocket broadcast for {event_name}")
