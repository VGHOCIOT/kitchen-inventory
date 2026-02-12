from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.item import Item, Locations
from uuid import UUID
import events
import logging

logger = logging.getLogger(__name__)

async def get_item_by_product_and_location(
    db,
    product_reference_id: UUID,
    location: Locations,
):
    result = await db.execute(
        select(Item).where(
            Item.product_reference_id == product_reference_id,
            Item.location == location,
        )
    )
    return result.scalar_one_or_none()

async def create_item(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
    qty: int = 1,
    expires_at: None = None,
) -> Item:
    """Create a new item. Assumes item doesn't already exist."""
    new_item = Item(
        product_reference_id=product_reference_id,
        location=location,
        qty=qty,
        expires_at=expires_at,
    )

    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    await events.emit("item_added", new_item)
    return new_item




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

async def move_item(
    db,
    product_reference_id: UUID,
    from_location: Locations,
    to_location: Locations,
    quantity: int,
):
    await adjust_item_quantity(
        db,
        product_reference_id,
        from_location,
        -quantity,
    )

    return await adjust_item_quantity(
        db,
        product_reference_id,
        to_location,
        quantity,
    )

async def adjust_item_quantity(
    db,
    product_reference_id: UUID,
    location: Locations,
    delta: int,
) -> Item | None:
    item = await get_item_by_product_and_location(
        db,
        product_reference_id,
        location,
    )

    if item:
        new_qty = item.qty + delta

        if new_qty <= 0:
            await db.delete(item)
            await db.commit()
            return None

        item.qty = new_qty
        await db.commit()
        await db.refresh(item)
        return item


async def delete_item_by_composite_key(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
) -> bool:
    """Delete item by composite key (product_reference_id, location)"""
    item = await get_item_by_product_and_location(db, product_reference_id, location)
    if item:
        await db.delete(item)
        await db.commit()
        await events.emit("item_deleted", item)
        return True
    return False
