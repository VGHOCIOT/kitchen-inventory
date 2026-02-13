from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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

from api.services.openfood import lookup_barcode
from schemas.item import (
    ItemOut,
    ScanIn,
    ScanOut,
    AdjustQuantityIn,
    MoveItemIn,
    DeleteItemIn,
)
from models.item import Locations

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
