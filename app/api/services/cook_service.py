"""
Cooking service — deducts recipe ingredients from inventory.

Reuses the recipe matcher's inventory aggregation, then deducts
required amounts from lots per ingredient.
"""

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from crud.item import get_all_items_with_products, deduct_stock
from crud.ingredient_alias import get_alias_by_text
from crud.ingredient_reference import get_ingredient_by_id
from crud.recipe import get_recipe_by_id
from crud.recipe_ingredient import get_recipe_ingredients
from api.services.recipe_matcher import aggregate_inventory_by_ingredient
from api.services.unit_converter import convert_to_base_unit

logger = logging.getLogger(__name__)


async def _build_ingredient_to_items_map(db: AsyncSession) -> dict[UUID, list[dict]]:
    """
    Build a map of ingredient_id → list of inventory item locations.
    Used to know which product+location to deduct from for a given ingredient.
    """
    items_with_products = await get_all_items_with_products(db)
    ingredient_to_items: dict[UUID, list[dict]] = {}

    for entry in items_with_products:
        item = entry["item"]
        product = entry["product"]

        if not product or not product.name:
            continue

        alias = await get_alias_by_text(db, product.name)
        if not alias:
            continue

        ingredient_id = alias.ingredient_id
        if ingredient_id not in ingredient_to_items:
            ingredient_to_items[ingredient_id] = []

        ingredient_to_items[ingredient_id].append({
            "product_reference_id": item.product_reference_id,
            "location": item.location,
            "qty": item.qty,
            "unit": item.unit,
        })

    return ingredient_to_items


async def cook_recipe(db: AsyncSession, recipe_id: UUID) -> dict | None:
    """
    Deduct all recipe ingredient quantities from inventory.

    Returns:
        {
            "recipe_title": str,
            "deducted": [{"ingredient": str, "amount": float, "unit": str}],
            "insufficient": [{"ingredient": str, "needed": float, "available": float, "unit": str}],
            "unmapped": [str]
        }
    """
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        return None

    recipe_ingredients = await get_recipe_ingredients(db, recipe_id)

    # Reuse the matcher's aggregation for availability check
    inventory = await aggregate_inventory_by_ingredient(db)

    # Also build the item-level map for deduction targets
    ingredient_to_items = await _build_ingredient_to_items_map(db)

    deducted = []
    insufficient = []
    unmapped = []

    for recipe_ing in recipe_ingredients:
        ingredient = await get_ingredient_by_id(db, recipe_ing.canonical_ingredient_id)
        if not ingredient:
            logger.warning(f"[COOK] Ingredient not found: {recipe_ing.canonical_ingredient_id}")
            continue

        required = await convert_to_base_unit(
            recipe_ing.quantity,
            recipe_ing.unit,
            ingredient.name,
        )
        needed = required["quantity"]
        needed_unit = required["base_unit"]

        # Check availability via aggregated inventory
        inv_data = inventory.get(recipe_ing.canonical_ingredient_id)

        if not inv_data:
            unmapped.append(ingredient.name)
            logger.warning(f"[COOK] No inventory for '{ingredient.name}'")
            continue

        if inv_data.base_unit != needed_unit:
            unmapped.append(ingredient.name)
            logger.warning(f"[COOK] Unit mismatch for '{ingredient.name}': {inv_data.base_unit} vs {needed_unit}")
            continue

        if inv_data.total_quantity < needed:
            insufficient.append({
                "ingredient": ingredient.name,
                "needed": needed,
                "available": inv_data.total_quantity,
                "unit": needed_unit,
            })
            continue

        # Deduct from inventory items for this ingredient
        inv_items = ingredient_to_items.get(recipe_ing.canonical_ingredient_id, [])
        remaining_to_deduct = needed

        for inv_item in inv_items:
            if remaining_to_deduct <= 0:
                break
            if inv_item["unit"] != needed_unit:
                continue

            deduct_amount = min(inv_item["qty"], remaining_to_deduct)
            await deduct_stock(
                db,
                product_reference_id=inv_item["product_reference_id"],
                location=inv_item["location"],
                amount=deduct_amount,
                unit=needed_unit,
            )
            remaining_to_deduct -= deduct_amount

        deducted.append({
            "ingredient": ingredient.name,
            "amount": needed,
            "unit": needed_unit,
        })
        logger.info(f"[COOK] Deducted {needed}{needed_unit} of '{ingredient.name}'")

    return {
        "recipe_title": recipe.title,
        "deducted": deducted,
        "insufficient": insufficient,
        "unmapped": unmapped,
    }
