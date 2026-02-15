from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.product_reference import ProductReference, ProductType
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


async def get_product_by_name(
    db: AsyncSession,
    name: str,
    product_type: ProductType = ProductType.PLU
) -> ProductReference | None:
    """Get a product by exact name match (primarily for PLU items)"""
    result = await db.execute(
        select(ProductReference).where(
            ProductReference.name == name,
            ProductReference.product_type == product_type
        )
    )
    return result.scalar_one_or_none()


async def create_product(
    db: AsyncSession,
    name: str,
    barcode: str | None = None,
    product_type: ProductType = ProductType.UPC,
    brands: list[str] | None = None,
    categories: list[str] | None = None,
    package_quantity: float | None = None,
    package_unit: str | None = None,
    product_data: dict | None = None
) -> ProductReference:
    """Create a new product reference (UPC with barcode or PLU without)"""
    new_prod_ref = ProductReference(
        product_type=product_type,
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

    identifier = f"barcode: {barcode}" if barcode else "PLU item"
    logger.info(f"Created new {product_type.value.upper()} product reference: {new_prod_ref.name} ({identifier})")
    events.emit("product_added", new_prod_ref)
    return new_prod_ref