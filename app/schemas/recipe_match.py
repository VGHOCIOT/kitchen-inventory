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

    class Config:
        from_attributes = True


class RecipeMatchResult(BaseModel):
    """Match result for a single recipe"""
    recipe_id: UUID
    recipe_title: str
    match_type: str  # "exact", "missing_ingredients", "with_substitutions"
    availability_percent: float  # 0-100
    ingredient_availability: list[IngredientAvailability]
    missing_ingredients: list[str]
    suggested_substitutions: list[SubstitutionSuggestion]

    class Config:
        from_attributes = True


class RecipeMatchResponse(BaseModel):
    """Complete recipe matching response with categorized results"""
    can_make_now: list[RecipeMatchResult]
    missing_one: list[RecipeMatchResult]
    missing_few: list[RecipeMatchResult]
    with_substitutions: list[RecipeMatchResult]
    total_recipes_checked: int

    class Config:
        from_attributes = True
