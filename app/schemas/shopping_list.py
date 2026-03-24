from pydantic import BaseModel
from uuid import UUID


class ShoppingListRequest(BaseModel):
    recipe_ids: list[UUID]


class ShoppingListItem(BaseModel):
    ingredient_id: UUID
    ingredient_name: str
    required_quantity: float
    available_quantity: float
    to_buy_quantity: float
    unit: str
    from_recipes: list[str]


class ShoppingListResponse(BaseModel):
    items: list[ShoppingListItem]
    fully_stocked: list[str]
    recipe_count: int
