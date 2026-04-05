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
from crud.ingredient_substitution import get_substitutions_for_ingredient
from api.services.recipe_matcher import (
    aggregate_inventory_by_ingredient,
    find_substitutions_for_ingredient,
)
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


async def _deduct_ingredient(
    db: AsyncSession,
    ingredient_id: UUID,
    needed: float,
    needed_unit: str,
    ingredient_to_items: dict[UUID, list[dict]],
) -> bool:
    """Deduct a specific ingredient from inventory items. Returns True if successful."""
    inv_items = ingredient_to_items.get(ingredient_id, [])
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

    return remaining_to_deduct <= 0


async def cook_recipe(
    db: AsyncSession,
    recipe_id: UUID,
    substitutions: dict[str, str] | None = None,
) -> dict | None:
    """
    Deduct all recipe ingredient quantities from inventory.

    Args:
        substitutions: Optional map of original_ingredient_id → substitute_ingredient_id.
            When provided, uses the substitute instead of the original ingredient.
            When not provided, auto-finds substitutes for missing/insufficient ingredients.

    Returns:
        {
            "recipe_title": str,
            "deducted": [{"ingredient": str, "amount": float, "unit": str}],
            "substituted": [{"original": str, "substitute": str, "amount": float, "unit": str, "ratio": float}],
            "insufficient": [{"ingredient": str, "needed": float, "available": float, "unit": str}],
            "unmapped": [str]
        }
    """
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        return None

    # Parse substitution overrides (string UUIDs → UUID objects)
    sub_overrides: dict[UUID, UUID] = {}
    if substitutions:
        for orig_str, sub_str in substitutions.items():
            sub_overrides[UUID(orig_str)] = UUID(sub_str)

    recipe_ingredients = await get_recipe_ingredients(db, recipe_id)

    # Reuse the matcher's aggregation for availability check
    inventory = await aggregate_inventory_by_ingredient(db)

    # Also build the item-level map for deduction targets
    ingredient_to_items = await _build_ingredient_to_items_map(db)

    deducted = []
    substituted = []
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

        ing_id = recipe_ing.canonical_ingredient_id

        # Check if there's an explicit substitution override for this ingredient
        if ing_id in sub_overrides:
            sub_id = sub_overrides[ing_id]
            sub_ingredient = await get_ingredient_by_id(db, sub_id)
            if not sub_ingredient:
                unmapped.append(ingredient.name)
                continue

            # Find the substitution rule for the ratio
            subs = await get_substitutions_for_ingredient(db, ing_id)
            ratio = 1.0
            for s in subs:
                if s.substitute_ingredient_id == sub_id:
                    ratio = s.ratio
                    break

            adjusted_amount = needed * ratio
            success = await _deduct_ingredient(
                db, sub_id, adjusted_amount, needed_unit, ingredient_to_items
            )
            if success:
                substituted.append({
                    "original": ingredient.name,
                    "substitute": sub_ingredient.name,
                    "amount": adjusted_amount,
                    "unit": needed_unit,
                    "ratio": ratio,
                })
                logger.info(f"[COOK] Substituted {adjusted_amount}{needed_unit} of '{sub_ingredient.name}' for '{ingredient.name}'")
                continue
            else:
                insufficient.append({
                    "ingredient": f"{sub_ingredient.name} (substitute for {ingredient.name})",
                    "needed": adjusted_amount,
                    "available": inventory.get(sub_id, None).total_quantity if inventory.get(sub_id) else 0.0,
                    "unit": needed_unit,
                })
                continue

        # Normal path: check availability via aggregated inventory
        inv_data = inventory.get(ing_id)

        # Try direct deduction if we have enough
        if inv_data and inv_data.base_unit == needed_unit and inv_data.total_quantity >= needed:
            success = await _deduct_ingredient(
                db, ing_id, needed, needed_unit, ingredient_to_items
            )
            if success:
                deducted.append({
                    "ingredient": ingredient.name,
                    "amount": needed,
                    "unit": needed_unit,
                })
                logger.info(f"[COOK] Deducted {needed}{needed_unit} of '{ingredient.name}'")
                continue

        # Ingredient missing or insufficient — try auto-substitution
        subs = await find_substitutions_for_ingredient(
            db, ing_id, inventory,
            required_quantity=needed,
            required_unit=needed_unit,
        )
        sub_suggestion = subs[0] if subs else None

        if sub_suggestion:
            adjusted_amount = needed * sub_suggestion.ratio
            success = await _deduct_ingredient(
                db,
                sub_suggestion.substitute_ingredient_id,
                adjusted_amount,
                needed_unit,
                ingredient_to_items,
            )
            if success:
                substituted.append({
                    "original": ingredient.name,
                    "substitute": sub_suggestion.substitute_ingredient_name,
                    "amount": adjusted_amount,
                    "unit": needed_unit,
                    "ratio": sub_suggestion.ratio,
                })
                logger.info(
                    f"[COOK] Auto-substituted {adjusted_amount}{needed_unit} of "
                    f"'{sub_suggestion.substitute_ingredient_name}' for '{ingredient.name}'"
                )
                continue

        # No substitution available — report as insufficient or unmapped
        if not inv_data:
            unmapped.append(ingredient.name)
            logger.warning(f"[COOK] No inventory for '{ingredient.name}'")
        elif inv_data.base_unit != needed_unit:
            unmapped.append(ingredient.name)
            logger.warning(f"[COOK] Unit mismatch for '{ingredient.name}': {inv_data.base_unit} vs {needed_unit}")
        else:
            insufficient.append({
                "ingredient": ingredient.name,
                "needed": needed,
                "available": inv_data.total_quantity,
                "unit": needed_unit,
            })

    return {
        "recipe_title": recipe.title,
        "deducted": deducted,
        "substituted": substituted,
        "insufficient": insufficient,
        "unmapped": unmapped,
    }
