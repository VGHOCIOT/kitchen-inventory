from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class RecipeCreateFromURL(BaseModel):
    url: str


class RecipeOut(BaseModel):
    id: UUID
    title: str
    instructions: list[str]
    source_url: Optional[str] = None

    class Config:
        from_attributes = True


class RecipeIngredientOut(BaseModel):
    id: UUID
    recipe_id: UUID
    ingredient_text: str
    canonical_ingredient_id: UUID
    quantity: float
    unit: str

    class Config:
        from_attributes = True


class RecipeWithIngredientsOut(BaseModel):
    recipe: RecipeOut
    ingredients: list[RecipeIngredientOut]
