"""
Receipt parser service - extracts line items from a grocery receipt image.

Uses Claude Vision API to read the receipt and return structured line items.
Each item includes product name, quantity, and weight (for fresh/PLU items).

The caller (endpoint) is responsible for matching items to ProductReferences
and writing to the database.
"""

import logging
from typing import Optional
from schemas.receipt import ReceiptLineItem
import anthropic
import os
import base64
import json

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

async def parse_receipt_image(
    image_bytes: bytes,
    mime_type: str,
    store_name: Optional[str] = None,
) -> tuple[list[ReceiptLineItem], list[str]]:
    """
    Send a receipt image to Claude Vision and extract structured line items.

    Returns a tuple of:
      - list[ReceiptLineItem]: successfully parsed product lines
      - list[str]: raw_text lines that couldn't be parsed (tax, totals, store info, etc.)

    Args:
        image_bytes: Raw image bytes from the uploaded file
        mime_type: MIME type of the image (e.g. "image/jpeg", "image/png")
        store_name: Optional store hint to help the model interpret abbreviations
                    (e.g. "Walmart", "Costco")
    """

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    receipt_prompt = _build_receipt_prompt(store_name)

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {
                "role":"user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_data
                        },
                    },
                    {
                        "type": "text",
                        "text": receipt_prompt
                    }
                ]
            }
        ]
    )

    try:
        result = json.loads(message.content[0].text)
    except json.JSONDecodeError as e:
        logger.warning(f"Faild to parse result correctly {e}")
        return [], []

    items, skipped = [], []
    for r in result:
        if r["skipped"]:
            skipped.append(r["raw_text"])
        else:
            r.pop("skipped")
            try:
                items.append(ReceiptLineItem(**r))
            except Exception as e:
                logger.warning(f"Failed to parse receipt item {r['raw_text']}: {e}")
    
    return items, skipped


def _build_receipt_prompt(store_name: Optional[str]) -> str:
    store_hint = f" The store is {store_name}, use it to resolve any known abbreviations for the store chain." if store_name else ""
    return (
        f"Identify each product line (skipping tax, subtotal, total, store header, loyalty points and the like).{store_hint}\n"
        "Return a JSON array where each element has these fields:\n"
        " raw_text (string) — the line exactly as printed\n"
        " product_name (string) — cleaned product name with any weight or size descriptor stripped out\n"
        "     e.g. 'Grape Tomatoes 283g' → 'Grape Tomatoes', 'PC Fresh Dill 28g' → 'PC Fresh Dill'\n"
        " quantity (number, default 1) — number of packages or units purchased\n"
        " weight_value (number or null) — set this whenever a weight appears, for BOTH:\n"
        "     - scale-weighed fresh items (e.g. bananas, deli meat with weight printed on line)\n"
        "     - pre-packaged items whose fixed weight appears in the product name or line (e.g. '283g', '1 kg')\n"
        "     Leave null only when no weight is mentioned anywhere on the line\n"
        " weight_unit (string or null) — e.g. 'kg', 'lb', 'g' — required when weight_value is set\n"
        " suggested_location (string) — where this item is typically stored:\n"
        "     FRIDGE for fresh produce, dairy, meat, deli\n"
        "     FREEZER for anything frozen\n"
        "     CUPBOARD for dry goods, canned, packaged shelf-stable items\n"
        " is_fresh_produce (boolean) — true for loose produce sold at a flat price per piece\n"
        "     with no weight on the receipt (e.g. lemon, avocado, individual apple)\n"
        "     false for all packaged goods and any item that has a weight\n"
        " skipped (boolean) — true for tax, totals, store header, loyalty points\n\n"
        "Return strict JSON array only — no markdown, no explanation."
    )
