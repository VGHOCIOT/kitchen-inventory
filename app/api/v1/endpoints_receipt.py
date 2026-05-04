"""
Receipt scanning endpoint.

POST /api/v1/receipt/scan
  - Accepts a multipart image upload of a grocery receipt
  - Parses line items via Claude Vision
  - For each line item: find or create a ProductReference, create a StockLot, refresh Item cache
  - Returns ReceiptScanOut with processed ScanOut entries and skipped lines
"""

import logging
from datetime import date, timedelta
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.services.shelf_life import estimate_shelf_life_days
from models.product_reference import ProductType
from schemas.receipt import ReceiptLineItem, ReceiptScanOut
from schemas.item import ScanOut
from api.services.receipt_parser import parse_receipt_image
from api.services.unit_converter import convert_to_base_unit
from api.services.ingredient_mapper import auto_map_product_to_ingredient
from config.fresh_weights import get_manual_weight
from crud.product_reference import get_product_by_name, create_product
from crud.item import add_stock

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Receipt"])

@router.post("/scan", response_model=ReceiptScanOut)
async def scan_receipt(
    image_file: UploadFile = File(...),
    store_name: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a grocery receipt image and bulk-add items to inventory.

    For each parsed line item:
    - Fresh/PLU items (weight_value present): convert receipt weight to grams,
      find or create a PLU ProductReference, create a StockLot with the weight
    - Packaged/UPC items (no weight): match by name to existing ProductReference,
      create a StockLot with package weight (or count if no package data)

    Location is inferred per item by the parser (FRIDGE/FREEZER/CUPBOARD).
    Unresolvable lines (tax, totals, store header) are returned in skipped[].
    """

    SUPPORTED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    EXT_FALLBACK = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}

    mime_type = image_file.content_type
    if mime_type not in SUPPORTED_TYPES:
        ext = (image_file.filename or "").lower().rsplit(".", 1)
        mime_type = EXT_FALLBACK.get(f".{ext[-1]}") if len(ext) == 2 else None
    if mime_type not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported image type. Must be one of: {', '.join(SUPPORTED_TYPES)}")

    MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
    image_bytes = await image_file.read()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 10 MB limit")

    items, skipped = await parse_receipt_image(image_bytes, mime_type, store_name)
    processed = []
    for item in items:
        if item.weight_value is not None or item.is_fresh_produce:
            result = await _process_fresh_item(db, item)
        else:
            result = await _process_packaged_item(db, item)
        if result:
            processed.append(result)

    return ReceiptScanOut(processed=processed, skipped=skipped)



async def _process_fresh_item(
    db: AsyncSession,
    item: ReceiptLineItem,
) -> ScanOut:
    """
    Handle a fresh/produce line item that has a weight printed on the receipt
    (e.g. "BANANAS   1.24 kg   $1.49").

    Converts weight to grams, creates a StockLot, and refreshes the Item cache.
    """
    if item.weight_value is not None:
        converted = await convert_to_base_unit(item.weight_value, item.weight_unit, item.product_name)
        lot_qty = converted["quantity"]
        lot_unit = converted["base_unit"]
    else:
        # Count-based fresh produce — look up per-unit weight from manual table
        weight_per_unit = get_manual_weight(item.product_name)
        if weight_per_unit:
            lot_qty = item.quantity * weight_per_unit
            lot_unit = "g"
        else:
            lot_qty = float(item.quantity)
            lot_unit = "unit"

    product_ref = await get_product_by_name(db, item.product_name, ProductType.PLU)

    if not product_ref:
        product_ref = await create_product(
            db,
            name=item.product_name,
            barcode=None,
            product_type=ProductType.PLU,
            brands=None,
            categories=None,
            package_quantity=1,
            package_unit=lot_unit,
            product_data={"entry_method": "receipt"},
        )

    await auto_map_product_to_ingredient(db, product_ref.name)

    expires_at = date.today() + timedelta(days=estimate_shelf_life_days(product_ref.name, item.suggested_location))
    inventory_item = await add_stock(
        db,
        product_reference_id=product_ref.id,
        location=item.suggested_location,
        quantity=lot_qty,
        unit=lot_unit,
        expires_at=expires_at,
    )

    return ScanOut(
        product_reference=product_ref,
        item=inventory_item,
        data_quality_warning=None,
    )


async def _process_packaged_item(
    db: AsyncSession,
    item: ReceiptLineItem,
) -> ScanOut:
    """
    Handle a packaged/UPC line item with no weight on the receipt
    (e.g. "TROPICANA OJ 1.75L   $4.99").

    If the product has package data (from a prior barcode scan), computes
    lot weight as item.quantity x package_quantity in base units.
    Otherwise falls back to count-based tracking.
    """
    product_ref = await get_product_by_name(db, item.product_name, ProductType.UPC)
    data_quality_warning = None

    if not product_ref:
        product_ref = await create_product(
            db,
            name=item.product_name,
            barcode=None,
            product_type=ProductType.UPC,
            brands=None,
            categories=None,
            package_quantity=None,
            package_unit=None,
            product_data={"entry_method": "receipt"},
        )
        data_quality_warning = (
            f"'{product_ref.name}' was created from a receipt with no barcode data. "
            f"Scan the barcode to get full package info for recipe matching."
        )

    has_package_data = product_ref.package_quantity is not None and product_ref.package_unit is not None
    if has_package_data:
        await auto_map_product_to_ingredient(db, product_ref.name)
        # Compute total weight: count from receipt x package weight
        conversion = await convert_to_base_unit(
            item.quantity * product_ref.package_quantity,
            product_ref.package_unit,
            product_ref.name,
        )
        lot_qty = conversion["quantity"]
        lot_unit = conversion["base_unit"]
    else:
        logger.warning(f"[RECEIPT] Skipping ingredient mapping for '{product_ref.name}' — incomplete package data")
        lot_qty = float(item.quantity)
        lot_unit = "unit"

    expires_at = date.today() + timedelta(days=estimate_shelf_life_days(product_ref.name, item.suggested_location))
    inventory_item = await add_stock(
        db,
        product_reference_id=product_ref.id,
        location=item.suggested_location,
        quantity=lot_qty,
        unit=lot_unit,
        expires_at=expires_at,
    )

    return ScanOut(
        product_reference=product_ref,
        item=inventory_item,
        data_quality_warning=data_quality_warning,
    )
