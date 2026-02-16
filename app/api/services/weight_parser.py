"""
Weight parser for extracting weight information from recipe ingredient text.

Looks for any weight-like patterns in the ingredient string.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_weight_from_text(ingredient_text: str) -> Optional[dict]:
    """
    Extract any weight hint from ingredient text.

    Looks for any number followed by weight units (lb, oz, g, kg) anywhere in the text.

    Args:
        ingredient_text: Original ingredient string

    Returns:
        {"quantity": float, "unit": str} or None if no weight found
    """
    if not ingredient_text:
        return None

    # Look for any number followed by weight units
    # Matches: "1.5 lb", "680g", "16 oz", "2.5kg", etc.
    weight_pattern = r'([0-9.]+)\s*(lb|lbs|pound|pounds|oz|ounce|ounces|g|grams|gram|kg|kilo|kilograms|kilogram)\b'

    matches = re.findall(weight_pattern, ingredient_text, re.IGNORECASE)

    if matches:
        # Use the first weight match found
        quantity_str, unit = matches[0]
        quantity = float(quantity_str)
        unit = unit.lower()

        logger.info(f"[WEIGHT] Found weight: {quantity} {unit} in '{ingredient_text}'")
        return {"quantity": quantity, "unit": unit}

    logger.debug(f"[WEIGHT] No weight found in '{ingredient_text}'")
    return None
