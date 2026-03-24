"""
Shopping list service — generates a consolidated list of what to buy
for a set of selected recipes, minus what's already in inventory.
"""

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from crud.recipe import get_recipe_by_id
from crud.recipe_ingredient import get_recipe_ingredients
from crud.ingredient_reference import get_ingredient_by_id
from api.services.recipe_matcher import aggregate_inventory_by_ingredient
from api.services.unit_converter import convert_to_base_unit
from schemas.shopping_list import ShoppingListItem, ShoppingListResponse

logger = logging.getLogger(__name__)


async def generate_shopping_list(
    db: AsyncSession,
    recipe_ids: list[UUID],
) -> ShoppingListResponse:
    """
    Generate a shopping list from selected recipes.

    1. Fetch all recipe ingredients for the given recipe IDs
    2. Consolidate by canonical_ingredient_id (sum across recipes)
    3. Subtract available inventory
    4. Return items where to_buy_quantity > 0
    """
    # Build inventory map (reuse matcher aggregation)
    inventory = await aggregate_inventory_by_ingredient(db)

    # Consolidate recipe ingredients across all selected recipes
    # ingredient_id → {needed, unit, recipe_titles}
    consolidated: dict[UUID, dict] = {}

    for recipe_id in recipe_ids:
        recipe = await get_recipe_by_id(db, recipe_id)
        if not recipe:
            logger.warning(f"[SHOPPING] Recipe not found: {recipe_id}")
            continue

        recipe_ingredients = await get_recipe_ingredients(db, recipe_id)

        for recipe_ing in recipe_ingredients:
            ingredient = await get_ingredient_by_id(db, recipe_ing.canonical_ingredient_id)
            if not ingredient:
                continue

            required = await convert_to_base_unit(
                recipe_ing.quantity,
                recipe_ing.unit,
                ingredient.name,
            )

            ing_id = recipe_ing.canonical_ingredient_id

            if ing_id in consolidated:
                consolidated[ing_id]["needed"] += required["quantity"]
                if recipe.title not in consolidated[ing_id]["from_recipes"]:
                    consolidated[ing_id]["from_recipes"].append(recipe.title)
            else:
                consolidated[ing_id] = {
                    "ingredient_name": ingredient.name,
                    "needed": required["quantity"],
                    "unit": required["base_unit"],
                    "from_recipes": [recipe.title],
                }

    # Compare against inventory
    items = []
    fully_stocked = []

    for ing_id, entry in consolidated.items():
        inv_data = inventory.get(ing_id)
        available = inv_data.total_quantity if inv_data else 0.0

        to_buy = entry["needed"] - available

        if to_buy <= 0:
            fully_stocked.append(entry["ingredient_name"])
        else:
            items.append(ShoppingListItem(
                ingredient_id=ing_id,
                ingredient_name=entry["ingredient_name"],
                required_quantity=entry["needed"],
                available_quantity=available,
                to_buy_quantity=to_buy,
                unit=entry["unit"],
                from_recipes=entry["from_recipes"],
            ))

    items.sort(key=lambda x: x.ingredient_name)

    return ShoppingListResponse(
        items=items,
        fully_stocked=sorted(fully_stocked),
        recipe_count=len(recipe_ids),
    )
