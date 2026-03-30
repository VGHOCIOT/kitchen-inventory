from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints_items import router as items_router
from api.v1.endpoints_recipes import router as recipes_router
from api.v1.endpoints_receipt import router as receipt_router
from api.v1.endpoints_shopping_list import router as shopping_list_router
from api.v1.endpoints_substitutions import router as substitutions_router
from api.v1.websocket import router as websocket_router
from db.session import SessionLocal
from db.seed import run_all_seeds

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run seeds
    async with SessionLocal() as db:
        try:
            await run_all_seeds(db)
        except Exception as e:
            logger.error(f"[STARTUP] Seed failed: {e}")
    yield


app = FastAPI(
    title="Kitchen Inventory API",
    description=(
        "Self-hosted kitchen inventory and recipe management system.\n\n"
        "**Core features:**\n"
        "- Barcode & receipt scanning to track groceries\n"
        "- Recipe parsing from URLs with ingredient normalization\n"
        "- Inventory-to-recipe matching with substitution support\n"
        "- Shopping list generation from selected recipes\n"
        "- FIFO stock lot tracking with location management"
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Inventory", "description": "Manage inventory items, scan barcodes, adjust quantities, cook recipes"},
        {"name": "Recipes", "description": "Parse recipes from URLs, match against inventory, manage recipe data"},
        {"name": "Receipt", "description": "Scan grocery receipts to bulk-add items"},
        {"name": "Shopping List", "description": "Generate shopping lists from selected recipes"},
        {"name": "Substitutions", "description": "Manage ingredient substitution rules"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items_router, prefix="/api/v1/items")
app.include_router(recipes_router, prefix="/api/v1/recipes")
app.include_router(receipt_router, prefix="/api/v1/receipt")
app.include_router(shopping_list_router, prefix="/api/v1/shopping-list")
app.include_router(substitutions_router, prefix="/api/v1/substitutions")
app.include_router(websocket_router)