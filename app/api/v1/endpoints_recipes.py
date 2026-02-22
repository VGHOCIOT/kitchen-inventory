from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from uuid import UUID

from crud.recipe import (
    create_recipe,
    get_recipe_by_id,
    get_all_recipes,
    delete_recipe,
)
from crud.recipe_ingredient import (
    create_recipe_ingredient,
    get_recipe_ingredients,
)
from crud.ingredient_reference import (
    create_ingredient_reference,
    get_ingredient_by_id,
    get_ingredient_by_name,
    get_ingredient_by_normalized_name,
)
from crud.ingredient_alias import get_alias_by_text

from api.services.recipe_parser import parse_recipe_from_url, normalize_ingredient_text
from api.services.spoonacular import parse_ingredients_batch
from api.services.recipe_matcher import match_all_recipes
from api.services.fresh_ingredient_service import get_weight_for_count_ingredient
from schemas.recipe import (
    RecipeCreateFromURL,
    RecipeOut,
    RecipeWithIngredientsOut,
)

router = APIRouter()


@router.post("/from-url", response_model=RecipeOut)
async def create_recipe_from_url(
    payload: RecipeCreateFromURL,
    db: AsyncSession = Depends(get_db)
):
    """
    Parse and save a recipe from a URL.
    Business logic orchestrates multiple CRUD operations.
    """
    # Parse recipe from URL
    recipe_data = await parse_recipe_from_url(payload.url)
    if not recipe_data:
        raise HTTPException(status_code=400, detail="Failed to parse recipe from URL")

    # Create the recipe
    recipe = await create_recipe(
        db,
        title=recipe_data["title"],
        instructions=recipe_data["instructions"],
        source_url=recipe_data["source_url"]
    )

    # Parse all ingredients with Spoonacular
    parsed_ingredients = await parse_ingredients_batch(recipe_data["ingredients"])

    # Process each ingredient
    for parsed in parsed_ingredients:
        # Normalize ingredient name for matching
        normalized = normalize_ingredient_text(parsed["name"])

        # Find or create ingredient (business logic in endpoint)
        ingredient_ref = await find_or_create_ingredient(db, normalized)

        # Determine quantity and unit with 3-tier fallback
        # 1. Spoonacular metric data (if available - currently not provided)
        # 2. Fresh ingredient weight lookup (for count-based items)
        # 3. Original parsed amount/unit

        if parsed.get("metric_amount") and parsed.get("metric_unit"):
            # Tier 1: Use Spoonacular metric data (when available)
            quantity = float(parsed["metric_amount"])
            unit = parsed["metric_unit"]
        elif not parsed["unit"] or parsed["unit"].strip() == "":
            # Tier 2: Count-based ingredient - try to get weight
            weight_data = await get_weight_for_count_ingredient(
                db,
                ingredient_ref,
                float(parsed["amount"]),
                parsed["original"]
            )
            if weight_data:
                quantity = weight_data["quantity"]
                unit = weight_data["unit"]
            else:
                # Fallback to count
                quantity = float(parsed["amount"])
                unit = parsed["unit"]
        else:
            # Tier 3: Use original parsed data
            quantity = float(parsed["amount"])
            unit = parsed["unit"]

        # Link ingredient to recipe with parsed quantity and unit
        await create_recipe_ingredient(
            db,
            recipe_id=recipe.id,
            ingredient_text=parsed["original"],
            canonical_ingredient_id=ingredient_ref.id,
            quantity=quantity,
            unit=unit
        )

    return recipe


@router.get("/", response_model=list[RecipeOut])
async def list_recipes(db: AsyncSession = Depends(get_db)):
    """List all recipes"""
    return await get_all_recipes(db)


@router.get("/match-inventory")
async def match_recipes_to_inventory(
    db: AsyncSession = Depends(get_db)
):
    """
    Match all recipes against current inventory.

    Returns categorized results showing which recipes can be made:
    - can_make_now: All ingredients available
    - missing_one: Missing exactly 1 ingredient
    - missing_few: Missing 2-3 ingredients
    - with_substitutions: Can make with ingredient substitutions
    """
    return await match_all_recipes(db)


@router.get("/{recipe_id}", response_model=RecipeWithIngredientsOut)
async def get_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get recipe with ingredients"""
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ingredients = await get_recipe_ingredients(db, recipe_id)

    return RecipeWithIngredientsOut(
        recipe=recipe,
        ingredients=ingredients
    )


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe_endpoint(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a recipe"""
    deleted = await delete_recipe(db, recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe not found")


# ============== HELPER FUNCTIONS (Business Logic) ==============

async def find_or_create_ingredient(db: AsyncSession, normalized_name: str):
    """
    Business logic: Find existing ingredient or create new one.
    This orchestrates multiple CRUD calls.
    """
    # Try exact match on name
    ingredient = await get_ingredient_by_name(db, normalized_name)
    if ingredient:
        return ingredient

    # Try match on normalized_name
    ingredient = await get_ingredient_by_normalized_name(db, normalized_name)
    if ingredient:
        return ingredient

    # Try match via alias
    alias = await get_alias_by_text(db, normalized_name)
    if alias:
        return await get_ingredient_by_id(db, alias.ingredient_id)

    # Not found - create new ingredient
    return await create_ingredient_reference(
        db,
        name=normalized_name,
        normalized_name=normalized_name
    )
