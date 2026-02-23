"""
Fresh ingredient service - orchestrates weight lookup from multiple sources.

3-tier lookup system:
1. Weight hint in recipe text (e.g., "(about 1.5 lb)")
2. Manual curated weights (config/fresh_weights.py)
3. USDA FNDDS API - purpose-built portion weight database (free, key required)

Results are cached in IngredientReference.avg_weight_grams for future use.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models.ingredient_reference import IngredientReference
from crud.ingredient_reference import update_avg_weight
from api.services.weight_parser import extract_weight_from_text
from api.services.unit_converter import convert_to_base_unit
from config.fresh_weights import get_manual_weight
from api.services.usda_api import get_average_weight as usda_get_weight

logger = logging.getLogger(__name__)


async def get_weight_for_count_ingredient(
    db: AsyncSession,
    ingredient_ref: IngredientReference,
    count: float,
    original_text: str
) -> Optional[dict]:
    """
    Get weight for a count-based ingredient (e.g., "2 chicken breasts").

    Checks cached weight first, then runs tiered lookup:
    1. Extract weight from original_text
    2. Manual weight table lookup
    3. USDA FNDDS API lookup

    Caches the per-unit weight in IngredientReference for future use.

    Args:
        db: Database session
        ingredient_ref: IngredientReference (resolved via alias)
        count: Number of units (e.g., 2)
        original_text: Original ingredient text from recipe

    Returns:
        {"quantity": float, "unit": str, "source": str} or None
    """
    ingredient_name = ingredient_ref.name
    logger.info(f"[FRESH] Looking up weight for {count} x '{ingredient_name}'")

    # Check if we have cached weight from previous lookup
    if ingredient_ref.avg_weight_grams:
        total_weight = count * ingredient_ref.avg_weight_grams
        logger.info(f"[FRESH] Using cached weight: {count} x {ingredient_ref.avg_weight_grams}g = {total_weight}g (source: {ingredient_ref.weight_source})")
        return {
            "quantity": total_weight,
            "unit": "g",
            "source": ingredient_ref.weight_source or "cached"
        }

    # No cached weight - run 3-tier lookup
    weight_per_unit = None
    source = None

    # Tier 1: Extract from recipe text
    weight_hint = extract_weight_from_text(original_text)
    if weight_hint:
        # Convert to grams
        conversion = await convert_to_base_unit(
            weight_hint["quantity"],
            weight_hint["unit"],
            ingredient_name
        )
        weight_per_unit = conversion["quantity"] / count  # Per-unit weight
        source = "recipe_text"
        logger.info(f"[FRESH] Extracted from recipe text: {weight_per_unit}g per unit")

    # Tier 2: Manual weight table
    if not weight_per_unit:
        manual_weight = get_manual_weight(ingredient_name)
        if manual_weight:
            weight_per_unit = manual_weight
            source = "manual"
            logger.info(f"[FRESH] Found in manual table: {weight_per_unit}g per unit")

    # Tier 3: USDA FNDDS lookup
    if not weight_per_unit:
        usda_weight = await usda_get_weight(ingredient_name)
        if usda_weight:
            weight_per_unit = usda_weight
            source = "usda"
            logger.info(f"[FRESH] Found via USDA FNDDS: {weight_per_unit}g per unit")

    # Cache the per-unit weight for future use
    if weight_per_unit and source:
        await update_avg_weight(db, ingredient_ref.id, weight_per_unit, source)
        total_weight = count * weight_per_unit
        logger.info(f"[FRESH] Cached weight for '{ingredient_name}': {weight_per_unit}g (source: {source})")
        return {
            "quantity": total_weight,
            "unit": "g",
            "source": source
        }

    # No weight data found
    logger.warning(f"[FRESH] No weight data found for '{ingredient_name}' - will use count-based ({count} unit)")
    return None
