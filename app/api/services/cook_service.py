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
from schemas.cook import CookPlan, CookPlanIngredient

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


async def get_cook_plan(db: AsyncSession, recipe_id: UUID) -> CookPlan | None:
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        return None

    recipe_ingredients = await get_recipe_ingredients(db, recipe_id)
    inventory = await aggregate_inventory_by_ingredient(db)

    plan_ingredients = []
    for recipe_ing in recipe_ingredients:
        ingredient = await get_ingredient_by_id(db, recipe_ing.canonical_ingredient_id)
        if not ingredient:
            continue

        required = await convert_to_base_unit(recipe_ing.quantity, recipe_ing.unit, ingredient.name)
        needed = required["quantity"]
        needed_unit = required["base_unit"]

        inv_data = inventory.get(recipe_ing.canonical_ingredient_id)
        available_qty = inv_data.total_quantity if inv_data else 0.0

        if inv_data and inv_data.base_unit == needed_unit and available_qty >= needed:
            status = 'available'
            substitutes = []
        else:
            status = 'missing' if not inv_data else 'insufficient'
            substitutes = await find_substitutions_for_ingredient(
                db, recipe_ing.canonical_ingredient_id, inventory,
                required_quantity=needed,
                required_unit=needed_unit,
            )

        plan_ingredients.append(CookPlanIngredient(
            recipe_ingredient_id=recipe_ing.id,
            ingredient_id=recipe_ing.canonical_ingredient_id,
            ingredient_name=ingredient.name,
            ingredient_text=recipe_ing.ingredient_text,
            quantity=recipe_ing.quantity,
            unit=recipe_ing.unit,
            status=status,
            available_quantity=available_qty,
            substitutes=substitutes,
        ))

    return CookPlan(
        recipe_id=recipe_id,
        recipe_title=recipe.title,
        ingredients=plan_ingredients,
    )


async def cook_recipe(
    db: AsyncSession,
    recipe_id: UUID,
    substitutions: dict[UUID, UUID] | None = None,
    skipped: list[UUID] | None = None,
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

    sub_overrides: dict[UUID, UUID] = substitutions or {}
    skip_set: set[UUID] = set(skipped) if skipped else set()

    recipe_ingredients = await get_recipe_ingredients(db, recipe_id)

    inventory = await aggregate_inventory_by_ingredient(db)
    ingredient_to_items = await _build_ingredient_to_items_map(db)

    # Pre-flight: verify all non-skipped ingredients can be fulfilled before deducting anything
    preflight_failed = []
    for recipe_ing in recipe_ingredients:
        ing_id = recipe_ing.canonical_ingredient_id
        if ing_id in skip_set:
            continue
        ingredient = await get_ingredient_by_id(db, ing_id)
        if not ingredient:
            continue
        required = await convert_to_base_unit(recipe_ing.quantity, recipe_ing.unit, ingredient.name)
        needed = required["quantity"]
        needed_unit = required["base_unit"]

        resolve_id = sub_overrides.get(ing_id, ing_id)
        inv_data = inventory.get(resolve_id)
        if not inv_data or inv_data.base_unit != needed_unit or inv_data.total_quantity < needed:
            if resolve_id == ing_id:
                # Try auto-sub to see if anything covers it
                subs = await find_substitutions_for_ingredient(db, ing_id, inventory, required_quantity=needed, required_unit=needed_unit)
                if not subs:
                    preflight_failed.append(ingredient.name)
            else:
                preflight_failed.append(ingredient.name)

    if preflight_failed:
        logger.warning(f"[COOK] Pre-flight failed for: {preflight_failed}")
        return {"recipe_title": recipe.title, "deducted": [], "failed": preflight_failed}

    deducted = []
    failed = []

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

        if ing_id in skip_set:
            continue

        # Manual override: use the specified substitute, don't fall through to auto-sub
        if ing_id in sub_overrides:
            sub_id = sub_overrides[ing_id]
            subs = await get_substitutions_for_ingredient(db, ing_id)
            ratio = next((s.ratio for s in subs if s.substitute_ingredient_id == sub_id), 1.0)
            adjusted = needed * ratio
            success = await _deduct_ingredient(db, sub_id, adjusted, needed_unit, ingredient_to_items)
            if success:
                sub_ingredient = await get_ingredient_by_id(db, sub_id)
                deducted.append({"ingredient": sub_ingredient.name, "amount": adjusted, "unit": needed_unit})
                logger.info(f"[COOK] Override: deducted {adjusted}{needed_unit} of '{sub_ingredient.name}' for '{ingredient.name}'")
            else:
                failed.append(ingredient.name)
                logger.warning(f"[COOK] Override substitute insufficient for '{ingredient.name}'")
            continue

        # Direct deduction
        inv_data = inventory.get(ing_id)
        if inv_data and inv_data.base_unit == needed_unit and inv_data.total_quantity >= needed:
            success = await _deduct_ingredient(db, ing_id, needed, needed_unit, ingredient_to_items)
            if success:
                deducted.append({"ingredient": ingredient.name, "amount": needed, "unit": needed_unit})
                logger.info(f"[COOK] Deducted {needed}{needed_unit} of '{ingredient.name}'")
                continue

        # Auto-substitution
        subs = await find_substitutions_for_ingredient(
            db, ing_id, inventory,
            required_quantity=needed,
            required_unit=needed_unit,
        )
        if subs:
            sub = subs[0]
            adjusted = needed * sub.ratio
            success = await _deduct_ingredient(
                db, sub.substitute_ingredient_id, adjusted, needed_unit, ingredient_to_items
            )
            if success:
                deducted.append({"ingredient": sub.substitute_ingredient_name, "amount": adjusted, "unit": needed_unit})
                logger.info(f"[COOK] Auto-sub: deducted {adjusted}{needed_unit} of '{sub.substitute_ingredient_name}' for '{ingredient.name}'")
                continue

        failed.append(ingredient.name)
        logger.warning(f"[COOK] Could not deduct '{ingredient.name}'")

    return {
        "recipe_title": recipe.title,
        "deducted": deducted,
        "failed": failed,
    }
