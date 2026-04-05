from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class SubstitutionCreate(BaseModel):
    original_ingredient_id: UUID
    substitute_ingredient_id: UUID
    ratio: float = 1.0
    quality_score: int = 3
    notes: Optional[str] = None


class SubstitutionOut(BaseModel):
    id: UUID
    original_ingredient_id: UUID
    original_ingredient_name: str
    substitute_ingredient_id: UUID
    substitute_ingredient_name: str
    ratio: float
    quality_score: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SubstitutionSeedResponse(BaseModel):
    created: int
    skipped: int
    ingredients_created: int
    message: str
