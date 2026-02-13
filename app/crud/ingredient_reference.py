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
