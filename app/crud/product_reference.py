from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.product_reference import ProductReference
from uuid import UUID
import events
import logging

logger = logging.getLogger(__name__)

async def get_product_by_barcode(
    db: AsyncSession,
    barcode: str
) -> ProductReference | None:
    result = await db.execute(select(ProductReference).where(ProductReference.barcode == barcode))
    return result.scalar_one_or_none()


async def create_product(
    db: AsyncSession,
    barcode: str,
    name: str | None = None,
    brands: list[str] | None = None,
    categories: list[str] | None = None,
    package_quantity: float | None = None,
    package_unit: str | None = None,
    product_data: dict | None = None
) -> ProductReference:

    new_prod_ref = ProductReference(
        barcode=barcode,
        name=name,
        brands=brands,
        categories=categories,
        package_quantity=package_quantity,
        package_unit=package_unit,
        meta_data=product_data
    )

    db.add(new_prod_ref)
    await db.commit()
    await db.refresh(new_prod_ref)
    logger.info(f"Created new product reference: {new_prod_ref.name} (barcode: {barcode})")
    events.emit("product_added", new_prod_ref)
    return new_prod_ref