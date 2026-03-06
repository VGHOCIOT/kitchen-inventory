from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
import logging

logger = logging.getLogger(__name__)

from crud.item import (
    get_all_items,
    get_items_by_location,
    get_item_by_product_and_location,
    create_item,
    adjust_item_quantity,
    move_item,
    delete_item_by_composite_key,
)
from crud.product_reference import (
    get_product_by_barcode,
    get_product_by_name,
    create_product,
)
from api.services.openfood import lookup_barcode
from api.services.ingredient_mapper import auto_map_product_to_ingredient
from schemas.item import (
    ItemOut,
    ScanIn,
    ScanOut,
    AdjustQuantityIn,
    MoveItemIn,
    DeleteItemIn,
)
from schemas.product_reference import CreateFreshItemIn
from models.item import Locations
from models.product_reference import ProductReference, ProductType

router = APIRouter()


# ============== READ OPERATIONS ==============

@router.get("/", response_model=list[ItemOut])
async def list_items(db: AsyncSession = Depends(get_db)):
    """List all items in inventory"""
    return await get_all_items(db)


@router.get("/location/{location}", response_model=list[ItemOut])
async def list_items_by_location(
    location: Locations,
    db: AsyncSession = Depends(get_db)
):
    """List all items at a specific location"""
    return await get_items_by_location(location, db)


# ============== SCAN OPERATION (Entry Point) ==============

@router.post("/scan", response_model=ScanOut)
async def scan_product(
    scan: ScanIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Scan a barcode to add item to inventory.
    - Looks up or creates ProductReference
    - Adds item to inventory (upsert: increments if exists, creates if not)
    """
    # Get or create product reference
    product_ref = await get_product_by_barcode(db, scan.barcode)

    if not product_ref:
        product_info = await lookup_barcode(scan.barcode)

        # Check data quality
        has_quantity = product_info.get("package_quantity") is not None
        has_unit = product_info.get("package_unit") is not None

        if not has_quantity or not has_unit:
            logger.warning(
                f"[SCAN] ⚠️  Incomplete product data for barcode {scan.barcode}: "
                f"quantity={product_info.get('package_quantity')}, unit={product_info.get('package_unit')}. "
                f"This product will NOT be usable for recipe matching."
            )

        product_ref = await create_product(
            db,
            name=product_info.get("name", f"Unknown product {scan.barcode}"),
            barcode=scan.barcode,
            product_type=ProductType.UPC,
            brands=product_info.get("brands", []),
            categories=product_info.get("categories", []),
            package_quantity=product_info.get("package_quantity"),
            package_unit=product_info.get("package_unit"),
            product_data=product_info or {},
        )

        # Auto-map product to ingredient for recipe matching (only if data is complete)
        if has_quantity and has_unit:
            await auto_map_product_to_ingredient(db, product_ref.name)
        else:
            logger.warning(f"[SCAN] Skipping ingredient mapping for '{product_ref.name}' - incomplete data")

    # Upsert logic: check if item exists at this location
    existing_item = await get_item_by_product_and_location(
        db, product_ref.id, scan.location
    )

    if existing_item:
        # Item exists - increment quantity using adjust
        item = await adjust_item_quantity(
            db, product_ref.id, scan.location, delta=1
        )
    else:
        # Item doesn't exist - create new
        item = await create_item(
            db, product_reference_id=product_ref.id, location=scan.location, qty=1
        )

    # Check if product has complete data for recipe matching
    data_warning = None
    if product_ref.package_quantity is None or product_ref.package_unit is None:
        data_warning = (
            f"⚠️  Product '{product_ref.name}' has incomplete quantity/unit data. "
            f"This product cannot be used for recipe matching. "
            f"Consider scanning a different barcode or manually updating product data."
        )

    return ScanOut(
        product_reference=product_ref,
        item=item,
        data_quality_warning=data_warning,
    )


@router.post("/add-fresh", response_model=ScanOut)
async def add_fresh_item(
    payload: CreateFreshItemIn,
    location: Locations = Locations.FRIDGE,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a fresh/weight-based item (PLU) to inventory without barcode.
    Used for produce, fresh meat, etc. that are weighed rather than scanned.

    This endpoint will be integrated with OCR receipt parsing in the future.
    """
    # Check if this fresh item already exists as a product
    product_ref = await get_product_by_name(db, payload.name, ProductType.PLU)

    if not product_ref:
        # Create new PLU product reference
        product_ref = await create_product(
            db,
            name=payload.name,
            barcode=None,  # No barcode for fresh items
            product_type=ProductType.PLU,
            brands=payload.brands,
            categories=payload.categories,
            package_quantity=payload.weight_grams,
            package_unit="g",  # Fresh items are always in grams
            product_data={"entry_method": "manual"},
        )

        # Auto-map product to ingredient for recipe matching
        await auto_map_product_to_ingredient(db, product_ref.name)

    # Upsert logic: check if item exists at this location
    existing_item = await get_item_by_product_and_location(
        db, product_ref.id, location
    )

    if existing_item:
        # Item exists - increment quantity
        item = await adjust_item_quantity(
            db, product_ref.id, location, delta=1
        )
    else:
        # Item doesn't exist - create new
        item = await create_item(
            db, product_reference_id=product_ref.id, location=location, qty=1
        )

    return ScanOut(
        product_reference=product_ref,
        item=item,
        data_quality_warning=None,
    )


# ============== INVENTORY MUTATIONS ==============

@router.patch("/adjust", response_model=ItemOut)
async def adjust_quantity(
    payload: AdjustQuantityIn,
    db: AsyncSession = Depends(get_db)
):
    """
    Adjust item quantity by delta.
    Uses composite key (product_reference_id, location).
    If quantity reaches 0 or below, item is deleted.
    """
    item = await adjust_item_quantity(
        db,
        product_reference_id=payload.product_reference_id,
        location=payload.location,
        delta=payload.delta,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found or quantity reached zero (item deleted)"
        )

    return item


@router.post("/move", response_model=ItemOut)
async def move_item_between_locations(
    payload: MoveItemIn,
    db: AsyncSession = Depends(get_db)
):
    """
    Move items between locations.
    Decrements from source, increments to destination.
    """
    item = await move_item(
        db,
        product_reference_id=payload.product_reference_id,
        from_location=payload.from_location,
        to_location=payload.to_location,
        quantity=payload.quantity,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found at source location or insufficient quantity"
        )

    return item


@router.delete("/", status_code=204)
async def delete_item(
    payload: DeleteItemIn,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete item by composite key (product_reference_id, location).
    """
    deleted = await delete_item_by_composite_key(
        db,
        product_reference_id=payload.product_reference_id,
        location=payload.location,
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")


# ============== UTILITY ENDPOINTS ==============

@router.post("/map-products-to-ingredients")
async def map_all_products_to_ingredients(db: AsyncSession = Depends(get_db)):
    """
    Utility endpoint to retroactively map all existing products to ingredients.
    Call this once after importing recipes to create ingredient aliases.
    """
    logger.info("[MAP_ALL] Starting product-to-ingredient mapping")

    # Get all products
    result = await db.execute(select(ProductReference))
    products = result.scalars().all()
    logger.info(f"[MAP_ALL] Found {len(products)} products to process")

    mapped_count = 0
    skipped_count = 0
    for product in products:
        existing_alias = await get_alias_by_text(db, product.name)
        if existing_alias:
            logger.info(f"[MAP_ALL] Skipped '{product.name}' - already mapped")
            skipped_count += 1
        else:
            # Try to map this product
            normalized = normalize_ingredient_text(product.name)
            if normalized:
                # Try exact match first
                ingredient = await get_ingredient_by_normalized_name(db, normalized)

                # If no exact match, try fuzzy matching
                if not ingredient:
                    logger.info(f"[MAP_ALL] No exact match, trying fuzzy match for '{product.name}'")
                    ingredient = await find_ingredient_fuzzy(db, normalized)

                if ingredient:
                    # Create alias for full product name
                    await create_ingredient_alias(db, alias=product.name, ingredient_id=ingredient.id)
                    logger.info(f"[MAP_ALL] ✓ Mapped '{product.name}' → '{ingredient.name}'")

                    # Also create alias for normalized name if different
                    if normalized != product.name and normalized != ingredient.name:
                        existing_normalized_alias = await get_alias_by_text(db, normalized)
                        if not existing_normalized_alias:
                            await create_ingredient_alias(db, alias=normalized, ingredient_id=ingredient.id)
                            logger.info(f"[MAP_ALL] ✓ Created normalized alias: '{normalized}' → '{ingredient.name}'")

                    mapped_count += 1
                else:
                    logger.warning(f"[MAP_ALL] ✗ No ingredient match (exact or fuzzy) for '{product.name}' (normalized: '{normalized}')")
            else:
                logger.warning(f"[MAP_ALL] ✗ Could not normalize '{product.name}'")

    logger.info(f"[MAP_ALL] Complete: {mapped_count} mapped, {skipped_count} skipped")
    return {
        "total_products": len(products),
        "newly_mapped": mapped_count,
        "already_mapped": skipped_count,
        "message": f"Successfully mapped {mapped_count} products to ingredients"
    }
