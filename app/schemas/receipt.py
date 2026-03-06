from pydantic import BaseModel
from typing import Optional
from schemas.item import ScanOut
from models.item import Locations


class ReceiptLineItem(BaseModel):
    """
    A single line item extracted from a receipt image by the vision model.

    For packaged goods (UPC): weight fields are None, quantity is unit count.
    For fresh/produce (PLU): weight_value + weight_unit hold what's printed on
    the receipt (e.g. weight_value=1.24, weight_unit="kg"), quantity defaults to 1.

    suggested_location is inferred by the model based on the product type
    (e.g. "FROZEN PEAS" → FREEZER, "BANANAS" → CUPBOARD, "CHICKEN" → FRIDGE).

    raw_text is preserved exactly as it appears on the receipt for debugging.
    """
    raw_text: str
    product_name: str
    quantity: int = 1
    weight_value: Optional[float] = None   # e.g. 1.24  — present for fresh/PLU items
    weight_unit: Optional[str] = None      # e.g. "kg", "lb", "g"
    suggested_location: Locations = Locations.FRIDGE


class ReceiptScanOut(BaseModel):
    """
    Full result of a receipt scan operation.
    processed contains one ScanOut per line item successfully added to inventory.
    skipped contains raw_text strings for lines the parser couldn't resolve
    (tax lines, totals, store header, etc.).
    """
    processed: list[ScanOut]
    skipped: list[str]
