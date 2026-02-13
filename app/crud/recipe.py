from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.recipe import Recipe
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


async def create_recipe(
    db: AsyncSession,
    title: str,
    instructions: list[str],
    source_url: str | None = None
) -> Recipe:
    """Create a new recipe"""
    recipe = Recipe(
        title=title,
        instructions=instructions,
        source_url=source_url
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)
    logger.info(f"Created recipe: {title}")
    return recipe


async def get_recipe_by_id(db: AsyncSession, recipe_id: UUID) -> Recipe | None:
    """Get recipe by ID"""
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    return result.scalar_one_or_none()


async def get_all_recipes(db: AsyncSession) -> list[Recipe]:
    """Get all recipes"""
    result = await db.execute(select(Recipe))
    return list(result.scalars().all())


async def delete_recipe(db: AsyncSession, recipe_id: UUID) -> bool:
    """Delete a recipe by ID"""
    recipe = await get_recipe_by_id(db, recipe_id)
    if recipe:
        await db.delete(recipe)
        await db.commit()
        return True
    return False
