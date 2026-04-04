"""
Shared service for automatically mapping a product name to a canonical ingredient.

Used by both the barcode scan endpoint and the receipt scan endpoint to ensure
newly created ProductReferences are wired up for recipe matching.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from crud.ingredient_alias import get_alias_by_text, create_ingredient_alias
from crud.ingredient_reference import get_ingredient_by_normalized_name, find_ingredient_fuzzy
from api.services.recipe_parser import normalize_product_name

logger = logging.getLogger(__name__)


async def auto_map_product_to_ingredient(db: AsyncSession, product_name: str):
    """
    Automatically map a product to a canonical ingredient.

    Process:
    1. Check if alias already exists
    2. Normalize product name (e.g., "Land O'Lakes Butter" → "butter")
    3. Find ingredient with exact normalized name match
    4. If no exact match, try fuzzy matching (substring matching)
    5. Create aliases for both product_name AND normalized_name → ingredient_id
       (this allows future similar products to match without fuzzy matching)
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
