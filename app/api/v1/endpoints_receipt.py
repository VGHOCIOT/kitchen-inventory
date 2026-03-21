"""
Receipt scanning endpoint.

POST /api/v1/receipt/scan
  - Accepts a multipart image upload of a grocery receipt
  - Parses line items via Claude Vision
  - For each line item: find or create a ProductReference, upsert an Item
  - Returns ReceiptScanOut with processed ScanOut entries and skipped lines
"""

import logging
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.product_reference import ProductType
from schemas.receipt import ReceiptLineItem, ReceiptScanOut
from schemas.item import ScanOut
from api.services.receipt_parser import parse_receipt_image
from api.services.unit_converter import convert_to_base_unit
from api.services.ingredient_mapper import auto_map_product_to_ingredient
from config.fresh_weights import get_manual_weight
from crud.product_reference import get_product_by_name, create_product
from crud.item import get_item_by_product_and_location, create_item, adjust_item_quantity

logger = logging.getLogger(__name__)
router = APIRouter()

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
      find or create a PLU ProductReference (package_quantity=1, package_unit="g"),
      upsert Item using qty as the qty delta — total qty = total grams held
    - Packaged/UPC items (no weight): match by name to existing ProductReference,
      create a UPC ProductReference if no match found, upsert Item

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

    image_bytes = await image_file.read()

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

    Steps:
    1. Convert item.weight_value + item.weight_unit to grams using convert_to_base_unit
    2. Look up an existing PLU ProductReference by name (get_product_by_name, ProductType.PLU)
       - If not found, create one with:
             product_type = ProductType.PLU
             package_quantity = 1
             package_unit = "g"
             product_data = {"entry_method": "receipt"}
       - package_quantity is always 1 so that Item.qty directly equals total grams held,
         allowing variable purchase weights to accumulate correctly across receipts
    3. Call auto_map_product_to_ingredient(db, product_ref.name) for recipe matching
    4. Upsert Item at item.suggested_location using qty as the delta:
       - If exists: adjust_item_quantity(delta=qty)
       - If not: create_item(qty=qty)
    5. Return ScanOut

    Args:
        db: Database session
        item: Parsed receipt line item with weight fields populated
    """
    if item.weight_value is not None:
        converted = await convert_to_base_unit(item.weight_value, item.weight_unit, item.product_name)
        qty = int(converted["quantity"])
        package_unit = "g"
    else:
        # Count-based fresh produce — look up per-unit weight from manual table
        weight_per_unit = get_manual_weight(item.product_name)
        if weight_per_unit:
            qty = int(item.quantity * weight_per_unit)
            package_unit = "g"
        else:
            qty = item.quantity
            package_unit = "unit"

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
            package_unit=package_unit,
            product_data={"entry_method": "receipt"},
        )

    await auto_map_product_to_ingredient(db, product_ref.name)

    existing_item = await get_item_by_product_and_location(
        db, product_ref.id, item.suggested_location
    )

    if existing_item:
        inventory_item = await adjust_item_quantity(
            db, product_ref.id, item.suggested_location, delta=qty
        )
    else:
        inventory_item = await create_item(
            db, product_reference_id=product_ref.id, location=item.suggested_location, qty=qty
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

    Receipts do not carry barcodes, so an OpenFoodFacts lookup is not possible here.
    Prefer matching an existing ProductReference by name — it may already have full
    package data from a prior barcode scan. Only create a minimal record if no match exists.

    Steps:
    1. Look up existing ProductReference by name (get_product_by_name, ProductType.UPC)
    2. If found: use it as-is — it already has barcode, package_quantity, package_unit
       from a previous OpenFoodFacts scan
    3. If not found: create a minimal UPC ProductReference and warn:
           product_type = ProductType.UPC
           barcode = None  (unavailable from receipt)
           name = item.product_name
           package_quantity/package_unit = None
           product_data = {"entry_method": "receipt"}
       → set data_quality_warning: product has no barcode/package data, rescan barcode for full info
    4. Call auto_map_product_to_ingredient(db, product_ref.name) for recipe matching
       (only if package data is complete — mirrors scan_product behaviour)
    5. Upsert Item at item.suggested_location using item.quantity as the delta
    6. Return ScanOut

    Args:
        db: Database session
        item: Parsed receipt line item without weight fields
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
            f"⚠️  '{product_ref.name}' was created from a receipt with no barcode data. "
            f"Scan the barcode to get full package info for recipe matching."
        )

    has_package_data = product_ref.package_quantity is not None and product_ref.package_unit is not None
    if has_package_data:
        await auto_map_product_to_ingredient(db, product_ref.name)
    else:
        logger.warning(f"[RECEIPT] Skipping ingredient mapping for '{product_ref.name}' — incomplete package data")

    existing_item = await get_item_by_product_and_location(
        db, product_ref.id, item.suggested_location
    )

    if existing_item:
        inventory_item = await adjust_item_quantity(
            db, product_ref.id, item.suggested_location, delta=item.quantity
        )
    else:
        inventory_item = await create_item(
            db, product_reference_id=product_ref.id, location=item.suggested_location, qty=item.quantity
        )

    return ScanOut(
        product_reference=product_ref,
        item=inventory_item,
        data_quality_warning=data_quality_warning,
    )

