from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.ingredient_alias import IngredientAlias
from uuid import UUID


async def create_ingredient_alias(
    db: AsyncSession,
    alias: str,
    ingredient_id: UUID
) -> IngredientAlias:
    """Create a new ingredient alias"""
    ingredient_alias = IngredientAlias(
        alias=alias,
        ingredient_id=ingredient_id
    )
    db.add(ingredient_alias)
    await db.commit()
    await db.refresh(ingredient_alias)
    return ingredient_alias


async def get_alias_by_text(db: AsyncSession, alias_text: str) -> IngredientAlias | None:
    """Get alias by text"""
    result = await db.execute(
        select(IngredientAlias).where(IngredientAlias.alias == alias_text)
    )
    return result.scalar_one_or_none()


async def get_aliases_for_ingredient(db: AsyncSession, ingredient_id: UUID) -> list[IngredientAlias]:
    """Get all aliases for an ingredient"""
    result = await db.execute(
        select(IngredientAlias).where(IngredientAlias.ingredient_id == ingredient_id)
    )
    return list(result.scalars().all())
