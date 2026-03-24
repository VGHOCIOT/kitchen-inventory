from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
import logging

logger = logging.getLogger(__name__)

from crud.item import (
    get_all_items,
    get_items_by_location,
    get_item_by_product_and_location,
    add_stock,
    deduct_stock,
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
from api.services.unit_converter import convert_to_base_unit
from api.services.cook_service import cook_recipe
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
from models.product_reference import ProductType

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
    - Creates a StockLot with the package weight converted to base units
    - Refreshes the Item cache (qty = total grams/ml across lots)
    """
    product_ref = await get_product_by_barcode(db, scan.barcode)

    if not product_ref:
        product_info = await lookup_barcode(scan.barcode)

        has_quantity = product_info.get("package_quantity") is not None
        has_unit = product_info.get("package_unit") is not None

        if not has_quantity or not has_unit:
            logger.warning(
                f"[SCAN] Incomplete product data for barcode {scan.barcode}: "
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

        if has_quantity and has_unit:
            await auto_map_product_to_ingredient(db, product_ref.name)
        else:
            logger.warning(f"[SCAN] Skipping ingredient mapping for '{product_ref.name}' - incomplete data")

    # Compute lot weight in base units
    data_warning = None
    if product_ref.package_quantity is not None and product_ref.package_unit is not None:
        conversion = await convert_to_base_unit(
            product_ref.package_quantity,
            product_ref.package_unit,
            product_ref.name,
        )
        lot_qty = conversion["quantity"]
        lot_unit = conversion["base_unit"]
    else:
        # Degraded mode: no package data, track as count
        lot_qty = 1.0
        lot_unit = "unit"
        data_warning = (
            f"'{product_ref.name}' has incomplete quantity/unit data. "
            f"This product cannot be used for recipe matching. "
            f"Consider scanning a different barcode or manually updating product data."
        )

    item = await add_stock(
        db,
        product_reference_id=product_ref.id,
        location=scan.location,
        quantity=lot_qty,
        unit=lot_unit,
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
    Creates a StockLot with the provided weight in grams.
    """
    product_ref = await get_product_by_name(db, payload.name, ProductType.PLU)

    if not product_ref:
        product_ref = await create_product(
            db,
            name=payload.name,
            barcode=None,
            product_type=ProductType.PLU,
            brands=payload.brands,
            categories=payload.categories,
            package_quantity=payload.weight_grams,
            package_unit="g",
            product_data={"entry_method": "manual"},
        )

        await auto_map_product_to_ingredient(db, product_ref.name)

    item = await add_stock(
        db,
        product_reference_id=product_ref.id,
        location=location,
        quantity=payload.weight_grams,
        unit="g",
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
    Adjust item quantity by delta (in base units: grams, ml, or count).
    Delta is a float — supports fractional amounts (e.g. -0.5 for half a lemon).
    Positive delta adds a new lot. Negative delta deducts from lots FIFO.
    If quantity reaches 0, item is deleted.
    """
    if payload.delta == 0:
        raise HTTPException(status_code=400, detail="Delta must be non-zero")

    # Need to know the unit — get from existing item
    existing = await get_item_by_product_and_location(
        db, payload.product_reference_id, payload.location
    )

    if payload.delta > 0:
        unit = existing.unit if existing else "unit"
        item = await add_stock(
            db,
            product_reference_id=payload.product_reference_id,
            location=payload.location,
            quantity=payload.delta,
            unit=unit,
        )
    else:
        if not existing:
            raise HTTPException(status_code=404, detail="Item not found")
        item = await deduct_stock(
            db,
            product_reference_id=payload.product_reference_id,
            location=payload.location,
            amount=abs(payload.delta),
            unit=existing.unit,
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
    Move stock between locations (in base units).
    Deducts from source lots FIFO, creates new lot at destination.
    """
    existing = await get_item_by_product_and_location(
        db, payload.product_reference_id, payload.from_location
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found at source location")

    item = await move_item(
        db,
        product_reference_id=payload.product_reference_id,
        from_location=payload.from_location,
        to_location=payload.to_location,
        quantity=payload.quantity,
        unit=existing.unit,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Insufficient quantity at source location"
        )

    return item


@router.delete("/", status_code=204)
async def delete_item(
    payload: DeleteItemIn,
    db: AsyncSession = Depends(get_db)
):
    """Delete item and all its lots by composite key."""
    deleted = await delete_item_by_composite_key(
        db,
        product_reference_id=payload.product_reference_id,
        location=payload.location,
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")


# ============== COOKING ==============

@router.post("/cook")
async def cook(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Cook a recipe — deducts all ingredient quantities from inventory.
    Walks lots FIFO per ingredient. Returns what was deducted and what was insufficient.
    """
    recipe_id = payload.get("recipe_id")
    if not recipe_id:
        raise HTTPException(status_code=400, detail="recipe_id is required")

    result = await cook_recipe(db, recipe_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return result
