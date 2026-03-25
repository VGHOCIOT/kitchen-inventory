from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ShoppingListRequest(BaseModel):
    recipe_ids: list[UUID]


class SubstitutionAvailable(BaseModel):
    substitute_ingredient_id: UUID
    substitute_ingredient_name: str
    ratio: float
    quality_score: int
    available_quantity: float
    unit: str


class ShoppingListItem(BaseModel):
    ingredient_id: UUID
    ingredient_name: str
    required_quantity: float
    available_quantity: float
    to_buy_quantity: float
    unit: str
    from_recipes: list[str]
    substitution_available: Optional[SubstitutionAvailable] = None


class ShoppingListResponse(BaseModel):
    items: list[ShoppingListItem]
    fully_stocked: list[str]
    recipe_count: int
