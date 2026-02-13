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
