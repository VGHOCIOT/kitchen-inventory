from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
import logging

from models.stock_lot import StockLot
from models.item import Item, Locations

logger = logging.getLogger(__name__)


async def create_lot(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
    quantity: float,
    unit: str,
    expires_at=None,
) -> StockLot:
    lot = StockLot(
        product_reference_id=product_reference_id,
        location=location,
        initial_quantity=quantity,
        remaining_quantity=quantity,
        unit=unit,
        expires_at=expires_at,
    )
    db.add(lot)
    await db.flush()
    return lot


async def get_lots_for_item(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
) -> list[StockLot]:
    """Get all lots for a product+location, ordered FEFO (earliest expiry first, nulls last)."""
    result = await db.execute(
        select(StockLot)
        .where(
            StockLot.product_reference_id == product_reference_id,
            StockLot.location == location,
            StockLot.remaining_quantity > 0,
        )
        .order_by(StockLot.expires_at.asc().nullslast(), StockLot.created_at.asc())
    )
    return list(result.scalars().all())


async def deduct_from_lots(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
    amount: float,
) -> float:
    """Walk lots FIFO and subtract amount. Returns actual amount deducted."""
    lots = await get_lots_for_item(db, product_reference_id, location)
    remaining_to_deduct = amount
    total_deducted = 0.0

    for lot in lots:
        if remaining_to_deduct <= 0:
            break

        deduct = min(lot.remaining_quantity, remaining_to_deduct)
        lot.remaining_quantity -= deduct
        remaining_to_deduct -= deduct
        total_deducted += deduct

        if lot.remaining_quantity <= 0:
            await db.delete(lot)

    await db.flush()
    return total_deducted


async def refresh_item_cache(
    db: AsyncSession,
    product_reference_id: UUID,
    location: Locations,
    unit: str,
) -> Item | None:
    """Recalculate Item.qty and Item.expires_at as SUM/MIN across active lots."""
    result = await db.execute(
        select(func.sum(StockLot.remaining_quantity))
        .where(
            StockLot.product_reference_id == product_reference_id,
            StockLot.location == location,
        )
    )
    total = result.scalar() or 0.0

    result_expires = await db.execute(
        select(func.min(StockLot.expires_at)).where(
            StockLot.product_reference_id == product_reference_id,
            StockLot.location == location,
            StockLot.remaining_quantity > 0,
            StockLot.expires_at.isnot(None),
        )
    )
    min_expires = result_expires.scalar()

    # Get or create the Item cache row
    item_result = await db.execute(
        select(Item).where(
            Item.product_reference_id == product_reference_id,
            Item.location == location,
        )
    )
    item = item_result.scalar_one_or_none()

    if total <= 0:
        # No remaining stock — remove cache row
        if item:
            await db.delete(item)
        await db.commit()
        return None

    if item:
        item.qty = total
        item.unit = unit
        item.expires_at = min_expires
    else:
        item = Item(
            product_reference_id=product_reference_id,
            location=location,
            qty=total,
            unit=unit,
            expires_at=min_expires,
        )
        db.add(item)

    await db.commit()
    await db.refresh(item)
    return item
