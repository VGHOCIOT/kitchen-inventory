from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class IngredientAvailability(BaseModel):
    """Availability status for a single ingredient in a recipe"""
    ingredient_id: UUID
    ingredient_name: str
    required_quantity: float
    available_quantity: float
    unit: str
    is_sufficient: bool

    class Config:
        from_attributes = True


class SubstitutionSuggestion(BaseModel):
    """Suggested ingredient substitution"""
    original_ingredient_id: UUID
    original_ingredient_name: str
    substitute_ingredient_id: UUID
    substitute_ingredient_name: str
    ratio: float
    quality_score: int
    notes: Optional[str] = None
    max_scale: Optional[float] = None
    substitute_quantity: Optional[float] = None
    substitute_unit: Optional[str] = None

    class Config:
        from_attributes = True


class RecipeMatchResult(BaseModel):
    """Match result for a single recipe"""
    recipe_id: UUID
    recipe_title: str
    recipe_description: Optional[str] = None
    recipe_image_url: Optional[str] = None
    match_type: str  # "unlocked", "almost", "locked"
    availability_percent: float  # 0-100, substitutions count as covered
    ingredient_availability: list[IngredientAvailability]
    missing_ingredients: list[str]
    suggested_substitutions: list[SubstitutionSuggestion]

    class Config:
        from_attributes = True


class RecipeMatchResponse(BaseModel):
    """Complete recipe matching response with gamified lock states.

    availability_percent counts substitutions as covered ingredients.
      unlocked: 100%
      almost:   >= 70%
      locked:   < 70%
    """
    unlocked: list[RecipeMatchResult]
    almost: list[RecipeMatchResult]
    locked: list[RecipeMatchResult]
    total_recipes_checked: int

    class Config:
        from_attributes = True
