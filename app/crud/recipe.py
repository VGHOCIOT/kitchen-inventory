from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.recipe import Recipe
from uuid import UUID
import logging
import events 
logger = logging.getLogger(__name__)


async def create_recipe(
    db: AsyncSession,
    title: str,
    instructions: list[str],
    source_url: str | None = None,
    description: str | None = None,
    image_url: str | None = None,
) -> Recipe:
    """Create a new recipe."""
    recipe = Recipe(
        title=title,
        description=description,
        image_url=image_url,
        instructions=instructions,
        source_url=source_url,
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)

    events.emit('recipe_added', { 
        'id': str(recipe.id),
        'title': recipe.title,
        'description': recipe.description,
        'image_url': recipe.image_url,
        'instructions': recipe.instructions,
        'source_url': recipe.source_url
    })
    logger.info(f"Created recipe: {title}")
    return recipe


async def get_recipe_by_source_url(db: AsyncSession, source_url: str) -> Recipe | None:
    """Get recipe by source URL"""
    result = await db.execute(select(Recipe).where(Recipe.source_url == source_url))
    return result.scalar_one_or_none()


async def get_recipe_by_title(db: AsyncSession, title: str) -> Recipe | None:
    """Get recipe by exact title (case-insensitive)"""
    result = await db.execute(
        select(Recipe).where(Recipe.title.ilike(title))
    )
    return result.scalar_one_or_none()


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
        
        events.emit('recipe_deleted', { 'id': str(recipe_id) })
        return True
    return False
