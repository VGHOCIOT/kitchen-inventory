from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.item import Item
from app.api.services.openfood import lookup_barcode
import logging

logger = logging.getLogger(__name__)

# Core async CRUD functions
async def get_or_create_from_barcode(barcode: str, location: str = "fridge", db: AsyncSession = None) -> Item:
    stmt = select(Item).where(Item.barcode == barcode)
    result = await db.execute(stmt)
    existing_item = result.scalar_one_or_none()

    if existing_item:
        if existing_item.location != location:
            existing_item.location = location
            await db.commit()
            await db.refresh(existing_item)
        return existing_item

    # If not found, fetch product info
    product_info = await lookup_barcode(barcode) or {
        "name": f"Unknown Product {barcode}",
        "brand": None,
        "category": None,
        "image_url": None
    }

    new_item = Item(
        barcode=barcode,
        name=product_info["name"],
        brand=product_info["brand"],
        category=product_info["category"],
        location=location,
        image_url=product_info["image_url"]
    )

    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    logger.info(f"Created new item: {new_item.name} (barcode: {barcode})")
    return new_item

async def get_item_by_id(item_id: int, db: AsyncSession) -> Item | None:
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()

async def get_item_by_barcode(barcode: str, db: AsyncSession) -> Item | None:
    result = await db.execute(select(Item).where(Item.barcode == barcode))
    return result.scalar_one_or_none()

async def get_items_by_location(location: str, db: AsyncSession) -> list[Item]:
    result = await db.execute(select(Item).where(Item.location == location))
    return result.scalars().all()

async def update_item_location(item_id: int, new_location: str, db: AsyncSession) -> Item | None:
    item = await get_item_by_id(item_id, db)
    if item:
        item.location = new_location
        await db.commit()
        await db.refresh(item)
    return item

async def delete_item(item_id: int, db: AsyncSession) -> bool:
    item = await get_item_by_id(item_id, db)
    if item:
        await db.delete(item)
        await db.commit()
        return True
    return False

async def get_all_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(select(Item))
    return result.scalars().all()
