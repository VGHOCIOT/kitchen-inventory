"""
Shared service for automatically mapping a product name to a canonical ingredient.

Used by both the barcode scan endpoint and the receipt scan endpoint to ensure
newly created ProductReferences are wired up for recipe matching.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from crud.ingredient_alias import get_alias_by_text, create_ingredient_alias
from crud.ingredient_reference import get_ingredient_by_id, get_ingredient_by_normalized_name, find_ingredient_fuzzy
from api.services.recipe_parser import normalize_product_name

logger = logging.getLogger(__name__)


async def auto_map_product_to_ingredient(db: AsyncSession, product_name: str):
    """
    Automatically map a product to a canonical ingredient.

    Process:
    1. Check if alias already exists for the full product name
    2. Normalize product name (strip brand/quality qualifiers)
    3. Check if normalized name is a known alias (e.g. "whole grain flour" → "whole wheat flour")
    4. Fuzzy match against existing ingredient normalized names (longest match wins)
    5. Exact normalized name match fallback
    6. Create alias for product_name → ingredient, and normalized_name if different
    """
    logger.info(f"[AUTO_MAP] Attempting to map product: '{product_name}'")

    existing_alias = await get_alias_by_text(db, product_name)
    if existing_alias:
        logger.info(f"[AUTO_MAP] Product '{product_name}' already has alias")
        return

    normalized = normalize_product_name(product_name)

    if not normalized:
        logger.warning(f"[AUTO_MAP] Failed to normalize product name: '{product_name}'")
        return

    # Check if the normalized name itself is a known alias (e.g. "whole grain flour" → "whole wheat flour")
    normalized_alias = await get_alias_by_text(db, normalized)
    if normalized_alias:
        ingredient_from_alias = await get_ingredient_by_id(db, normalized_alias.ingredient_id)
        if ingredient_from_alias:
            await create_ingredient_alias(db, alias=product_name, ingredient_id=ingredient_from_alias.id)
            logger.info(f"[AUTO_MAP] ✓ Created alias via normalized alias lookup: '{product_name}' → '{ingredient_from_alias.name}'")
            return

    # Try fuzzy match first — prefers existing ingredients over creating new ones.
    # e.g. "virgin olive oil" fuzzy-matches existing "olive oil" rather than
    # exact-matching a non-existent "virgin olive oil" and creating a duplicate.
    ingredient = await find_ingredient_fuzzy(db, normalized)

    if not ingredient:
        logger.info(f"[AUTO_MAP] No fuzzy match, trying exact normalized match for: '{normalized}'")
        ingredient = await get_ingredient_by_normalized_name(db, normalized)

    if ingredient:
        await create_ingredient_alias(db, alias=product_name, ingredient_id=ingredient.id)
        logger.info(f"[AUTO_MAP] ✓ Created alias: '{product_name}' → '{ingredient.name}'")

        if normalized != product_name and normalized != ingredient.name:
            existing_normalized_alias = await get_alias_by_text(db, normalized)
            if not existing_normalized_alias:
                await create_ingredient_alias(db, alias=normalized, ingredient_id=ingredient.id)
                logger.info(f"[AUTO_MAP] ✓ Created normalized alias: '{normalized}' → '{ingredient.name}'")
    else:
        logger.warning(f"[AUTO_MAP] ✗ No ingredient found (exact or fuzzy) for normalized name: '{normalized}'")
