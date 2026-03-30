from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from uuid import UUID

from crud.ingredient_substitution import (
    get_all_substitutions,
    get_substitutions_for_ingredient,
    create_substitution,
    delete_substitution,
)
from crud.ingredient_reference import get_ingredient_by_id
from schemas.ingredient_substitution import SubstitutionCreate, SubstitutionOut

router = APIRouter(tags=["Substitutions"])


async def _resolve_substitution_out(db: AsyncSession, sub) -> SubstitutionOut:
    """Resolve ingredient names for a substitution record."""
    original = await get_ingredient_by_id(db, sub.original_ingredient_id)
    substitute = await get_ingredient_by_id(db, sub.substitute_ingredient_id)
    return SubstitutionOut(
        id=sub.id,
        original_ingredient_id=sub.original_ingredient_id,
        original_ingredient_name=original.name if original else "unknown",
        substitute_ingredient_id=sub.substitute_ingredient_id,
        substitute_ingredient_name=substitute.name if substitute else "unknown",
        ratio=sub.ratio,
        quality_score=sub.quality_score,
        notes=sub.notes,
    )


@router.get("/", response_model=list[SubstitutionOut])
async def list_substitutions(db: AsyncSession = Depends(get_db)):
    """List all substitution rules."""
    subs = await get_all_substitutions(db)
    return [await _resolve_substitution_out(db, s) for s in subs]


@router.get("/{ingredient_id}", response_model=list[SubstitutionOut])
async def list_substitutions_for_ingredient(
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all substitution rules for a specific ingredient."""
    subs = await get_substitutions_for_ingredient(db, ingredient_id)
    return [await _resolve_substitution_out(db, s) for s in subs]


@router.post("/", response_model=SubstitutionOut, status_code=201)
async def create_substitution_endpoint(
    payload: SubstitutionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new substitution rule."""
    original = await get_ingredient_by_id(db, payload.original_ingredient_id)
    if not original:
        raise HTTPException(status_code=404, detail="Original ingredient not found")

    substitute = await get_ingredient_by_id(db, payload.substitute_ingredient_id)
    if not substitute:
        raise HTTPException(status_code=404, detail="Substitute ingredient not found")

    sub = await create_substitution(
        db,
        original_ingredient_id=payload.original_ingredient_id,
        substitute_ingredient_id=payload.substitute_ingredient_id,
        ratio=payload.ratio,
        quality_score=payload.quality_score,
        notes=payload.notes,
    )
    return await _resolve_substitution_out(db, sub)


@router.delete("/{substitution_id}", status_code=204)
async def delete_substitution_endpoint(
    substitution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a substitution rule."""
    deleted = await delete_substitution(db, substitution_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Substitution not found")
