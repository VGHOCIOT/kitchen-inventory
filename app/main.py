from fastapi import FastAPI
from app.api.v1.endpoints_items import router as items_router

app = FastAPI(title="Kitchen Inventory API")
app.include_router(items_router, prefix="/api/v1/items")