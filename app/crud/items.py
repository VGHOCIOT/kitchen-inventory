from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.item import Item
from api.services.openfood import lookup_barcode
import events
import logging

logger = logging.getLogger(__name__)

async def scan_barcode(
    db: AsyncSession,
    barcode: str,
    location: str = "fridge"
) -> Item:
    existing = await get_item_by_barcode(barcode, db)

    if existing:
        existing = move_item(existing.id, location, db)
        exiting = adjust_item_quantity(exiting.id, 1, db)

    product_info = await lookup_barcode(barcode)

    return await create_item(
        db,
        barcode,
        location,
        name = product_info.get("name") if product_info else f"Unknown product {barcode}",
        brands = product_info.get("brands") if product_info else [],
        categories = product_info.get("categories") if product_info else [],
        product_data = product_info or {},
    )

async def create_item(
    db: AsyncSession, 
    barcode: str,
    location: str = "fridge",
    name: str | None = None,
    qty: int = 1,
    expiry: None = None, # to be updated when implemented
    brands: list[str] | None = None,
    categories: list[str] | None = None,
    product_data: dict | None = None
) -> Item:

    new_item = Item(
        barcode,
        location,
        name,
        qty,
        expiry,
        brands,
        categories,
        product_data
    )

    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    logger.info(f"Created new item: {new_item.name} (barcode: {barcode})")
    await events.emit("item_added", new_item)
    return new_item

async def get_item_by_barcode(barcode: str, db: AsyncSession) -> Item:
    result = await db.execute(select(Item).where(Item.barcode == barcode))
    return result.scalar_one_or_none()

async def get_item_by_id(item_id: int, db: AsyncSession) -> Item | None:
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()

async def get_items_by_location(location: str, db: AsyncSession) -> list[Item]:
    result = await db.execute(select(Item).where(Item.location == location))
    return result.scalars().all()

async def get_all_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(select(Item))
    return result.scalars().all()

async def move_item(
        item_id: int,
        new_location: str,
        db: AsyncSession
) -> Item | None:
    item = await get_item_by_id(item_id, db)
    if not item: 
        return None
    
    if item.location != new_location:
        item.location = new_location
        await db.commit()
        await db.refresh(item)

    return item

async def adjust_item_quantity(
    item_id: int,
    delta: int,
    db: AsyncSession
) -> Item | None:
    item = await get_item_by_id(item_id, db)
    if not item:
        return None

    if delta == 0:
        return item

    new_qty = item.qty + delta

    if new_qty <= 0:
        await db.delete(item)
        await db.commit()
        return None

    item.qty = new_qty
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
