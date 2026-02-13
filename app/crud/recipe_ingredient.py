from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.recipe_ingredient import RecipeIngredient
from uuid import UUID


async def create_recipe_ingredient(
    db: AsyncSession,
    recipe_id: UUID,
    ingredient_text: str,
    canonical_ingredient_id: UUID,
    quantity: float,
    unit: str
) -> RecipeIngredient:
    """Create a recipe ingredient link"""
    recipe_ingredient = RecipeIngredient(
        recipe_id=recipe_id,
        ingredient_text=ingredient_text,
        canonical_ingredient_id=canonical_ingredient_id,
        quantity=quantity,
        unit=unit
    )
    db.add(recipe_ingredient)
    await db.commit()
    await db.refresh(recipe_ingredient)
    return recipe_ingredient


async def get_recipe_ingredients(db: AsyncSession, recipe_id: UUID) -> list[RecipeIngredient]:
    """Get all ingredients for a recipe"""
    result = await db.execute(
        select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
    )
    return list(result.scalars().all())


async def delete_recipe_ingredient(db: AsyncSession, recipe_ingredient_id: UUID) -> bool:
    """Delete a recipe ingredient by ID"""
    result = await db.execute(
        select(RecipeIngredient).where(RecipeIngredient.id == recipe_ingredient_id)
    )
    recipe_ingredient = result.scalar_one_or_none()
    if recipe_ingredient:
        await db.delete(recipe_ingredient)
        await db.commit()
        return True
    return False
