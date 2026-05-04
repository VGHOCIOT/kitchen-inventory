from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
import logging

logger = logging.getLogger(__name__)

from crud.item import (
    get_all_items_with_products,
    get_items_by_location,
    get_item_by_id,
    get_item_by_product_and_location,
    add_stock,
    adjust_item_quantity,
    move_item,
    delete_item_by_composite_key,
)
from crud.stock_lot import get_lots_for_item, update_lot_opened_at, update_lot_expires_at
from api.services.shelf_life import estimate_shelf_life_days
from schemas.stock_lot import StockLotUpdateIn
from crud.product_reference import (
    get_product_by_barcode,
    get_product_by_name,
    get_product_by_id,
    create_product,
    rename_product,
)
from api.services.openfood import lookup_barcode
from api.services.ingredient_mapper import auto_map_product_to_ingredient
from api.services.unit_converter import convert_to_base_unit
from api.services.cook_service import cook_recipe
from crud.ingredient_alias import get_alias_by_text
from crud.ingredient_reference import get_ingredient_by_id
from config.fresh_weights import get_manual_weight
from schemas.item import (
    ItemOut,
    ItemWithProductOut,
    StockLotOut,
    ScanLookupIn,
    ScanLookupOut,
    ScanIn,
    ScanOut,
    AdjustQuantityIn,
    MoveItemIn,
    DeleteItemIn,
    EditItemIn,
)
from schemas.product_reference import CreateFreshItemIn
from schemas.cook import CookRequest, CookResponse
from models.item import Locations
from models.product_reference import ProductType
from uuid import UUID as _UUID

router = APIRouter(tags=["Inventory"])


# ============== READ OPERATIONS ==============

@router.get("/", response_model=list[ItemWithProductOut])
async def list_items(db: AsyncSession = Depends(get_db)):
    """List all items in inventory with product details"""
    return await get_all_items_with_products(db)


@router.get("/lots/{product_reference_id}/{location}", response_model=list[StockLotOut])
async def list_lots_for_item(
    product_reference_id: str,
    location: Locations,
    db: AsyncSession = Depends(get_db),
):
    """List all active stock lots for a product at a location, ordered FEFO."""
    lots = await get_lots_for_item(db, _UUID(product_reference_id), location)
    return lots


@router.patch("/lots/{lot_id}", response_model=StockLotOut)
async def update_lot(
    lot_id: str,
    payload: StockLotUpdateIn,
    db: AsyncSession = Depends(get_db),
):
    """Update a lot: mark as opened (recomputes expiry from after-opening shelf life) or override expires_at directly."""
    if "expires_at" in payload.model_fields_set:
        lot = await update_lot_expires_at(db, _UUID(lot_id), payload.expires_at)
    else:
        lot = await update_lot_opened_at(db, _UUID(lot_id), payload.opened_at)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot


@router.get("/location/{location}", response_model=list[ItemOut])
async def list_items_by_location(
    location: Locations,
    db: AsyncSession = Depends(get_db)
):
    """List all items at a specific location"""
    return await get_items_by_location(location, db)


# ============== SCAN OPERATION (Entry Point) ==============

async def _resolve_product_and_compute_lot(
    db: AsyncSession,
    barcode: str,
) -> tuple:
    """
    Shared logic for lookup and confirm: resolve ProductReference, convert units.
    Returns (product_ref, lot_qty, lot_unit, requires_manual_entry).
    lot_qty/lot_unit are None when requires_manual_entry is True.
    """
    product_ref = await get_product_by_barcode(db, barcode)

    if not product_ref:
        product_info = await lookup_barcode(barcode)

        has_quantity = product_info.get("package_quantity") is not None
        has_unit = product_info.get("package_unit") is not None

        if not has_quantity or not has_unit:
            logger.warning(
                f"[SCAN] Incomplete product data for barcode {barcode}: "
                f"quantity={product_info.get('package_quantity')}, unit={product_info.get('package_unit')}. "
                f"This product will NOT be usable for recipe matching."
            )

        product_ref = await create_product(
            db,
            name=product_info.get("name", f"Unknown product {barcode}"),
            barcode=barcode,
            product_type=ProductType.UPC,
            brands=product_info.get("brands", []),
            categories=product_info.get("categories", []),
            package_quantity=product_info.get("package_quantity"),
            package_unit=product_info.get("package_unit"),
            product_data=product_info or {},
        )

    if product_ref.package_quantity and product_ref.package_unit:
        await auto_map_product_to_ingredient(db, product_ref.name)
    else:
        logger.warning(f"[SCAN] Skipping ingredient mapping for '{product_ref.name}' - incomplete data")

    if product_ref.package_quantity is None or product_ref.package_unit is None:
        return product_ref, None, None, True

    conversion = await convert_to_base_unit(
        product_ref.package_quantity,
        product_ref.package_unit,
        product_ref.name,
    )
    lot_qty = conversion["quantity"]
    lot_unit = conversion["base_unit"]

    # If conversion returned "unit" (count-based), try to convert to grams
    # using the ingredient's avg_weight_grams so inventory matches recipe units.
    if lot_unit == "unit":
        weight_per_unit = None
        alias = await get_alias_by_text(db, product_ref.name)
        if alias:
            ingredient = await get_ingredient_by_id(db, alias.ingredient_id)
            if ingredient and ingredient.avg_weight_grams:
                weight_per_unit = ingredient.avg_weight_grams
            elif ingredient:
                weight_per_unit = get_manual_weight(ingredient.name)

        if weight_per_unit:
            lot_qty = product_ref.package_quantity * weight_per_unit
            lot_unit = "g"
            logger.info(
                f"[SCAN] Converted {product_ref.package_quantity} units to "
                f"{lot_qty}g using avg_weight={weight_per_unit}g/unit"
            )

    return product_ref, lot_qty, lot_unit, False


@router.post("/scan/lookup", response_model=ScanLookupOut)
async def scan_lookup(
    scan: ScanLookupIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve a barcode to product info and computed lot qty/unit without writing to inventory.
    Creates ProductReference on first encounter (idempotent catalog write).
    Returns requires_manual_entry=True when package data is missing.
    """
    product_ref, lot_qty, lot_unit, requires_manual_entry = await _resolve_product_and_compute_lot(db, scan.barcode)

    if requires_manual_entry:
        logger.warning(f"[SCAN] Degraded mode for '{product_ref.name}' — requires manual entry")
        return ScanLookupOut(
            product_reference=product_ref,
            requires_manual_entry=True,
        )

    return ScanLookupOut(
        product_reference=product_ref,
        computed_qty=lot_qty,
        computed_unit=lot_unit,
    )


@router.post("/scan", response_model=ScanOut)
async def scan_product(
    scan: ScanIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Commit a scanned barcode to inventory.
    - Resolves or creates ProductReference (no-op if already exists from /scan/lookup)
    - Creates multiplier StockLots at the chosen location
    """
    product_ref, lot_qty, lot_unit, requires_manual_entry = await _resolve_product_and_compute_lot(db, scan.barcode)

    if requires_manual_entry:
        logger.warning(f"[SCAN] Degraded mode for '{product_ref.name}' — requires manual entry")
        return ScanOut(
            product_reference=product_ref,
            item=None,
            requires_manual_entry=True,
        )

    expires_at = date.today() + timedelta(days=estimate_shelf_life_days(product_ref.name, scan.location))
    item = await add_stock(
        db,
        product_reference_id=product_ref.id,
        location=scan.location,
        quantity=lot_qty * scan.multiplier,
        unit=lot_unit,
        expires_at=expires_at,
    )

    return ScanOut(
        product_reference=product_ref,
        item=item,
    )


@router.post("/add-fresh", response_model=ScanOut)
async def add_fresh_item(
    payload: CreateFreshItemIn,
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

    expires_at = date.today() + timedelta(days=estimate_shelf_life_days(product_ref.name, payload.location))
    item = await add_stock(
        db,
        product_reference_id=product_ref.id,
        location=payload.location,
        quantity=payload.weight_grams,
        unit="g",
        expires_at=expires_at,
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
    Positive delta adds a new lot. Negative delta deducts from lots FEFO.
    If quantity reaches 0, item is deleted.
    """
    if payload.delta == 0:
        raise HTTPException(status_code=400, detail="Delta must be non-zero")

    item = await adjust_item_quantity(db, payload.product_reference_id, payload.location, payload.delta)

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
    Deducts from source lots FEFO, creates new lot at destination.
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


@router.patch("/edit", response_model=ItemWithProductOut)
async def edit_item(
    payload: EditItemIn,
    db: AsyncSession = Depends(get_db),
):
    """Edit item qty, location, and/or product name (name change applies globally)."""
    if payload.qty is None and payload.name is None and payload.location is None:
        raise HTTPException(status_code=400, detail="At least one of qty, name, or location must be provided")

    item = await get_item_by_id(payload.item_id, db)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.name is not None:
        product = await rename_product(db, item.product_reference_id, payload.name.strip())
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        await auto_map_product_to_ingredient(db, product.name)

    if payload.location is not None and payload.location != item.location:
        item = await move_item(
            db,
            product_reference_id=item.product_reference_id,
            from_location=item.location,
            to_location=payload.location,
            quantity=item.qty,
            unit=item.unit,
        )
        if not item:
            raise HTTPException(status_code=400, detail="Failed to move item to new location")

    if payload.qty is not None:
        if payload.qty <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
        delta = payload.qty - item.qty
        if delta != 0:
            item = await adjust_item_quantity(db, item.product_reference_id, item.location, delta)
        if not item:
            raise HTTPException(status_code=400, detail="Quantity adjustment resulted in empty item")

    product = await get_product_by_id(db, item.product_reference_id)
    return {"item": item, "product": product}


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

@router.post("/cook", response_model=CookResponse)
async def cook(
    payload: CookRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cook a recipe — deducts all ingredient quantities from inventory.
    Walks lots FIFO per ingredient. Returns what was deducted and what was insufficient.

    Optionally pass `substitutions` as a mapping of original ingredient name to
    substitute ingredient name to force specific swaps.
    """
    result = await cook_recipe(
        db,
        str(payload.recipe_id),
        substitutions=payload.substitutions,
        skipped=payload.skipped,
        scale=payload.scale,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return result
