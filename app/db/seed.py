"""
Startup seed logic — runs once on app boot.

All seed functions are idempotent (skip existing rows),
so this is safe to run on every startup.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from config.ingredient_aliases import INGREDIENT_ALIAS_SEEDS
from config.ingredient_substitutions import INGREDIENT_SUBSTITUTION_SEEDS
from crud.ingredient_reference import (
    create_ingredient_reference,
    get_ingredient_by_normalized_name,
)
from crud.ingredient_alias import create_ingredient_alias, get_alias_by_text
from crud.ingredient_substitution import create_substitution, get_substitution_by_pair

logger = logging.getLogger(__name__)


async def _resolve_ingredient(db: AsyncSession, name: str):
    """Find or create a canonical IngredientReference by name."""
    ingredient = await get_ingredient_by_normalized_name(db, name)
    if not ingredient:
        ingredient = await create_ingredient_reference(
            db, name=name, normalized_name=name
        )
    return ingredient


async def seed_aliases(db: AsyncSession) -> dict:
    """Seed ingredient aliases from config. Idempotent."""
    created_aliases = 0
    skipped = 0

    for canonical_name, aliases in INGREDIENT_ALIAS_SEEDS.items():
        ingredient = await _resolve_ingredient(db, canonical_name)

        for alias_text in aliases:
            existing = await get_alias_by_text(db, alias_text)
            if existing:
                skipped += 1
                continue
            await create_ingredient_alias(db, alias=alias_text, ingredient_id=ingredient.id)
            created_aliases += 1

    logger.info(f"[SEED] Aliases: {created_aliases} created, {skipped} skipped")
    return {"aliases_created": created_aliases, "skipped": skipped}


async def seed_substitutions(db: AsyncSession) -> dict:
    """Seed ingredient substitutions from config. Idempotent."""
    created = 0
    skipped = 0

    for entry in INGREDIENT_SUBSTITUTION_SEEDS:
        original = await _resolve_ingredient(db, entry["original"])
        substitute = await _resolve_ingredient(db, entry["substitute"])

        # Forward direction
        if await get_substitution_by_pair(db, original.id, substitute.id):
            skipped += 1
        else:
            await create_substitution(
                db,
                original_ingredient_id=original.id,
                substitute_ingredient_id=substitute.id,
                ratio=entry["ratio"],
                quality_score=entry["quality_score"],
                notes=entry.get("notes"),
            )
            created += 1

        # Reverse direction (if bidirectional)
        if entry.get("bidirectional"):
            if await get_substitution_by_pair(db, substitute.id, original.id):
                skipped += 1
            else:
                reverse_ratio = round(1.0 / entry["ratio"], 2)
                reverse_notes = f"{entry.get('notes', '')} (reverse)".strip()
                await create_substitution(
                    db,
                    original_ingredient_id=substitute.id,
                    substitute_ingredient_id=original.id,
                    ratio=reverse_ratio,
                    quality_score=entry["quality_score"],
                    notes=reverse_notes,
                )
                created += 1

    logger.info(f"[SEED] Substitutions: {created} created, {skipped} skipped")
    return {"created": created, "skipped": skipped}


async def run_all_seeds(db: AsyncSession):
    """Run all seed functions on startup."""
    logger.info("[SEED] Running startup seeds...")
    await seed_aliases(db)
    await seed_substitutions(db)
    logger.info("[SEED] Startup seeds complete")
