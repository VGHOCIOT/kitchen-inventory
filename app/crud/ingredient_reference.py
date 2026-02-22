from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.ingredient_reference import IngredientReference
from uuid import UUID


async def create_ingredient_reference(
    db: AsyncSession,
    name: str,
    normalized_name: str | None = None,
    meta_data: dict | None = None
) -> IngredientReference:
    """Create a new ingredient reference"""
    ingredient = IngredientReference(
        name=name,
        normalized_name=normalized_name or name.lower(),
        meta_data=meta_data
    )
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


async def get_ingredient_by_id(db: AsyncSession, ingredient_id: UUID) -> IngredientReference | None:
    """Get ingredient by ID"""
    result = await db.execute(
        select(IngredientReference).where(IngredientReference.id == ingredient_id)
    )
    return result.scalar_one_or_none()


async def get_ingredient_by_name(db: AsyncSession, name: str) -> IngredientReference | None:
    """Get ingredient by exact name match"""
    result = await db.execute(
        select(IngredientReference).where(IngredientReference.name == name)
    )
    return result.scalar_one_or_none()


async def get_ingredient_by_normalized_name(db: AsyncSession, normalized_name: str) -> IngredientReference | None:
    """Get ingredient by normalized name match"""
    result = await db.execute(
        select(IngredientReference).where(IngredientReference.normalized_name == normalized_name)
    )
    return result.scalar_one_or_none()


async def get_all_ingredients(db: AsyncSession) -> list[IngredientReference]:
    """Get all ingredients"""
    result = await db.execute(select(IngredientReference))
    return list(result.scalars().all())


async def find_ingredient_fuzzy(db: AsyncSession, search_text: str) -> IngredientReference | None:
    """
    Find ingredient using fuzzy matching.
    Returns ingredient where normalized name is contained in search_text or vice versa.
    Prioritizes shorter matches (more specific ingredients).
    """
    all_ingredients = await get_all_ingredients(db)

    search_lower = search_text.lower()
    matches = []

    for ingredient in all_ingredients:
        ing_normalized = ingredient.normalized_name.lower()

        # Check if ingredient name is in search text or search text is in ingredient name
        if ing_normalized in search_lower or search_lower in ing_normalized:
            matches.append(ingredient)

    # If multiple matches, return the one with shortest normalized_name (most specific)
    if matches:
        return min(matches, key=lambda x: len(x.normalized_name))

    return None


async def update_avg_weight(
    db: AsyncSession,
    ingredient_id: UUID,
    avg_weight_grams: float,
    weight_source: str
) -> IngredientReference:
    """
    Update average weight for an ingredient.

    Args:
        db: Database session
        ingredient_id: UUID of ingredient to update
        avg_weight_grams: Average weight in grams
        weight_source: Source of weight data ("recipe_text", "manual", "usda", "user_override")

    Returns:
        Updated IngredientReference
    """
    ingredient = await get_ingredient_by_id(db, ingredient_id)
    if not ingredient:
        raise ValueError(f"Ingredient {ingredient_id} not found")

    ingredient.avg_weight_grams = avg_weight_grams
    ingredient.weight_source = weight_source

    await db.commit()
    await db.refresh(ingredient)
    return ingredient
