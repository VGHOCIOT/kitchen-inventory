from fastapi import FastAPI
from app.api.v1.endpoints_items import router as items_router
from app.api.v1.websocket import router as websocket_router

app = FastAPI(title="Kitchen Inventory API")
app.include_router(items_router, prefix="/api/v1/items")
app.include_router(websocket_router)