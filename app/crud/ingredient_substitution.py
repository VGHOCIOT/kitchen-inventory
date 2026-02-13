from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.ingredient_substitution import IngredientSubstitution
from uuid import UUID


async def get_substitutions_for_ingredient(
    db: AsyncSession,
    ingredient_id: UUID
) -> list[IngredientSubstitution]:
    """Get all possible substitutes for an ingredient"""
    result = await db.execute(
        select(IngredientSubstitution).where(
            IngredientSubstitution.original_ingredient_id == ingredient_id
        )
    )
    return list(result.scalars().all())


async def create_substitution(
    db: AsyncSession,
    original_ingredient_id: UUID,
    substitute_ingredient_id: UUID,
    ratio: float = 1.0,
    quality_score: int = 5,
    notes: str | None = None
) -> IngredientSubstitution:
    """Create new substitution rule"""
    substitution = IngredientSubstitution(
        original_ingredient_id=original_ingredient_id,
        substitute_ingredient_id=substitute_ingredient_id,
        ratio=ratio,
        quality_score=quality_score,
        notes=notes
    )
    db.add(substitution)
    await db.commit()
    await db.refresh(substitution)
    return substitution


async def get_substitution_by_id(
    db: AsyncSession,
    substitution_id: UUID
) -> IngredientSubstitution | None:
    """Get substitution by ID"""
    result = await db.execute(
        select(IngredientSubstitution).where(
            IngredientSubstitution.id == substitution_id
        )
    )
    return result.scalar_one_or_none()


async def delete_substitution(
    db: AsyncSession,
    substitution_id: UUID
) -> bool:
    """Delete a substitution rule"""
    substitution = await get_substitution_by_id(db, substitution_id)
    if not substitution:
        return False

    await db.delete(substitution)
    await db.commit()
    return True
