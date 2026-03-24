from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.item import Item, Locations
from models.product_reference import ProductReference
from uuid import UUID
import events
import logging

from crud.stock_lot import create_lot, deduct_from_lots, refresh_item_cache

logger = logging.getLogger(__name__)


async def get_item_by_product_and_location(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
) -> Item | None:
    result = await db.execute(
        select(Item).where(
            Item.product_reference_id == product_reference_id,
            Item.location == location,
        )
    )
    return result.scalar_one_or_none()


async def add_stock(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
    quantity: float,
    unit: str,
    expires_at=None,
) -> Item:
    """Add stock by creating a lot and refreshing the Item cache."""
    await create_lot(db, product_reference_id, location, quantity, unit, expires_at)
    item = await refresh_item_cache(db, product_reference_id, location, unit)

    events.emit("item_added", {
        "id": str(item.id),
        "product_reference_id": str(item.product_reference_id),
        "location": item.location.value,
        "qty": item.qty,
        "unit": item.unit,
    })
    return item


async def deduct_stock(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
    amount: float,
    unit: str,
) -> Item | None:
    """Deduct stock by walking lots FIFO. Returns updated Item or None if depleted."""
    actual_deducted = await deduct_from_lots(db, product_reference_id, location, amount)

    if actual_deducted <= 0:
        return None

    item = await refresh_item_cache(db, product_reference_id, location, unit)

    if item is None:
        events.emit("item_deleted", {
            "product_reference_id": str(product_reference_id),
            "location": location.value,
        })

    return item


async def get_item_by_id(item_id: UUID | str, db: AsyncSession) -> Item | None:
    if isinstance(item_id, str):
        try:
            item_id = UUID(item_id)
        except ValueError:
            logger.error(f"Invalid UUID format: {item_id}")
            return None

    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()


async def get_items_by_location(location: Locations, db: AsyncSession) -> list[Item]:
    result = await db.execute(select(Item).where(Item.location == location))
    return list(result.scalars().all())


async def get_all_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(select(Item))
    return list(result.scalars().all())


async def get_all_items_with_products(db: AsyncSession) -> list[dict]:
    """Get all items with joined ProductReference data for inventory aggregation."""
    result = await db.execute(
        select(Item, ProductReference).join(
            ProductReference,
            Item.product_reference_id == ProductReference.id
        )
    )

    items_with_products = []
    for item, product in result.all():
        items_with_products.append({
            "item": item,
            "product": product
        })

    return items_with_products


async def move_item(
    db: AsyncSession,
    product_reference_id: UUID,
    from_location: Locations,
    to_location: Locations,
    quantity: float,
    unit: str,
) -> Item | None:
    """Move stock between locations by deducting from source and adding to destination."""
    actual_deducted = await deduct_from_lots(
        db, product_reference_id, from_location, quantity
    )

    if actual_deducted <= 0:
        return None

    await create_lot(db, product_reference_id, to_location, actual_deducted, unit)
    await refresh_item_cache(db, product_reference_id, from_location, unit)
    item = await refresh_item_cache(db, product_reference_id, to_location, unit)

    return item


async def delete_item_by_composite_key(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
) -> bool:
    """Delete item and all its lots by composite key."""
    from models.stock_lot import StockLot

    # Delete all lots for this product+location
    result = await db.execute(
        select(StockLot).where(
            StockLot.product_reference_id == product_reference_id,
            StockLot.location == location,
        )
    )
    lots = result.scalars().all()
    for lot in lots:
        await db.delete(lot)

    # Delete the item cache row
    item = await get_item_by_product_and_location(db, product_reference_id, location)
    if item:
        await db.delete(item)
        await db.commit()
        events.emit("item_deleted", {
            "id": str(item.id),
            "product_reference_id": str(item.product_reference_id),
            "location": item.location.value,
        })
        return True

    await db.commit()
    return False
