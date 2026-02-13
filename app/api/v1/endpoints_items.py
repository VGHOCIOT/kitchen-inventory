from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db

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
    create_product,
)
from crud.ingredient_alias import (
    get_alias_by_text,
    create_ingredient_alias,
)
from crud.ingredient_reference import (
    get_ingredient_by_normalized_name,
)

from api.services.openfood import lookup_barcode
from api.services.recipe_parser import normalize_ingredient_text
from schemas.item import (
    ItemOut,
    ScanIn,
    ScanOut,
    AdjustQuantityIn,
    MoveItemIn,
    DeleteItemIn,
)
from models.item import Locations
from models.product_reference import ProductReference

router = APIRouter()


# ============== HELPER FUNCTIONS ==============

async def auto_map_product_to_ingredient(db: AsyncSession, product_name: str):
    """
    Automatically map a product to a canonical ingredient.

    Process:
    1. Check if alias already exists
    2. Normalize product name (e.g., "Land O'Lakes Butter" → "butter")
    3. Find ingredient with matching normalized name
    4. Create alias mapping product_name → ingredient_id
    """
    # Check if alias already exists
    existing_alias = await get_alias_by_text(db, product_name)
    if existing_alias:
        return  # Already mapped

    # Normalize the product name to find base ingredient
    normalized = normalize_ingredient_text(product_name)

    if not normalized:
        return  # Can't normalize, skip

    # Try to find ingredient by normalized name
    ingredient = await get_ingredient_by_normalized_name(db, normalized)

    if ingredient:
        # Create alias mapping product → ingredient
        await create_ingredient_alias(db, alias=product_name, ingredient_id=ingredient.id)


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
        product_ref = await create_product(
            db,
            barcode=scan.barcode,
            name=product_info.get("name", f"Unknown product {scan.barcode}"),
            brands=product_info.get("brands", []),
            categories=product_info.get("categories", []),
            package_quantity=product_info.get("package_quantity"),
            package_unit=product_info.get("package_unit"),
            product_data=product_info or {},
        )

        # Auto-map product to ingredient for recipe matching
        await auto_map_product_to_ingredient(db, product_ref.name)

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

    return ScanOut(
        product_reference=product_ref,
        item=item,
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
    # Get all products
    result = await db.execute(select(ProductReference))
    products = result.scalars().all()

    mapped_count = 0
    for product in products:
        existing_alias = await get_alias_by_text(db, product.name)
        if not existing_alias:
            # Try to map this product
            normalized = normalize_ingredient_text(product.name)
            if normalized:
                ingredient = await get_ingredient_by_normalized_name(db, normalized)
                if ingredient:
                    await create_ingredient_alias(db, alias=product.name, ingredient_id=ingredient.id)
                    mapped_count += 1

    return {
        "total_products": len(products),
        "newly_mapped": mapped_count,
        "message": f"Successfully mapped {mapped_count} products to ingredients"
    }
