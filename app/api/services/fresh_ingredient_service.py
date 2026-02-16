"""
Fresh ingredient service - orchestrates weight lookup from multiple sources.

3-tier lookup system:
1. Weight hint in recipe text (e.g., "(about 1.5 lb)")
2. Manual curated weights (config/fresh_weights.py)
3. USDA FoodData Central API (fallback)
"""

import logging
from typing import Optional
from api.services.weight_parser import extract_weight_from_text
from api.services.unit_converter import convert_to_base_unit
from config.fresh_weights import get_manual_weight
from api.services.usda_api import get_average_weight

logger = logging.getLogger(__name__)


async def get_weight_for_count_ingredient(
    ingredient_name: str,
    count: float,
    original_text: str
) -> Optional[dict]:
    """
    Get weight for a count-based ingredient (e.g., "2 chicken breasts").

    Tries in order:
    1. Extract weight from original_text
    2. Manual weight table lookup
    3. USDA API lookup

    Args:
        ingredient_name: Normalized ingredient name (e.g., "chicken breast")
        count: Number of units (e.g., 2)
        original_text: Original ingredient text from recipe

    Returns:
        {"quantity": float, "unit": str, "source": str} or None
    """
    logger.info(f"[FRESH] Looking up weight for {count} x '{ingredient_name}'")

    # Tier 1: Extract from recipe text
    weight_hint = extract_weight_from_text(original_text)
    if weight_hint:
        # Convert to grams
        conversion = await convert_to_base_unit(
            weight_hint["quantity"],
            weight_hint["unit"],
            ingredient_name
        )

        logger.info(f"[FRESH] Using weight from recipe text: {conversion['quantity']} {conversion['base_unit']} (source: recipe_text)")
        return {
            "quantity": conversion["quantity"],
            "unit": conversion["base_unit"],
            "source": "recipe_text"
        }

    # Tier 2: Manual weight table
    manual_weight_per_unit = get_manual_weight(ingredient_name)
    if manual_weight_per_unit:
        total_weight = count * manual_weight_per_unit
        logger.info(f"[FRESH] Using manual weight: {count} x {manual_weight_per_unit}g = {total_weight}g (source: manual)")
        return {
            "quantity": total_weight,
            "unit": "g",
            "source": "manual"
        }

    # Tier 3: USDA API lookup
    usda_weight_per_unit = await get_average_weight(ingredient_name)
    if usda_weight_per_unit:
        total_weight = count * usda_weight_per_unit
        logger.info(f"[FRESH] Using USDA weight: {count} x {usda_weight_per_unit}g = {total_weight}g (source: usda)")
        return {
            "quantity": total_weight,
            "unit": "g",
            "source": "usda"
        }

    # No weight data found
    logger.warning(f"[FRESH] No weight data found for '{ingredient_name}' - will use count-based ({count} unit)")
    return None
