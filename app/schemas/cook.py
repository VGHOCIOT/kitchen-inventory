from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID
from schemas.recipe_match import SubstitutionSuggestion


class CookRequest(BaseModel):
    recipe_id: UUID
    substitutions: Optional[dict[UUID, UUID]] = None
    skipped: Optional[list[UUID]] = None
    scale: float = 1.0


class DeductedItem(BaseModel):
    ingredient: str
    amount: float
    unit: str


class CookResponse(BaseModel):
    recipe_title: str
    deducted: list[DeductedItem]
    failed: list[str]


class CookPlanIngredient(BaseModel):
    recipe_ingredient_id: UUID
    ingredient_id: UUID
    ingredient_name: str
    ingredient_text: str
    quantity: float
    unit: str
    status: Literal['available', 'insufficient', 'missing']
    available_quantity: float
    substitutes: list[SubstitutionSuggestion]
    max_scale: Optional[float] = None


class CookPlan(BaseModel):
    recipe_id: UUID
    recipe_title: str
    ingredients: list[CookPlanIngredient]
