"""
Recipe matching service for inventory-to-recipe matching.

Aggregates inventory by ingredient and determines which recipes can be made
with current items, including substitution suggestions.
"""

from dataclasses import dataclass
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from models.recipe import Recipe
from crud.item import get_all_items_with_products
from crud.ingredient_alias import get_alias_by_text
from crud.ingredient_reference import get_ingredient_by_id
from crud.ingredient_substitution import get_substitutions_for_ingredient
from crud.recipe import get_all_recipes
from crud.recipe_ingredient import get_recipe_ingredients
from api.services.unit_converter import convert_to_base_unit
from schemas.recipe_match import (
    RecipeMatchResponse,
    RecipeMatchResult,
    IngredientAvailability,
    SubstitutionSuggestion
)

logger = logging.getLogger(__name__)


@dataclass
class InventoryIngredient:
    """Aggregated inventory data for a single ingredient"""
    ingredient_id: UUID
    ingredient_name: str
    total_quantity: float
    base_unit: str  # "g", "ml", or "unit"
    product_references: list[dict]  # Track which products contribute


async def aggregate_inventory_by_ingredient(
    db: AsyncSession
) -> dict[UUID, InventoryIngredient]:
    """
    Build inventory map: ingredient_id → total available quantity.

    Item.qty is already stored in base units (g, ml, or unit count),
    so no package_quantity multiplication or unit conversion is needed.

    Process:
    1. Query all Items with ProductReference data
    2. Map each product to its canonical ingredient via IngredientAlias
    3. Use Item.qty directly (already in base units)
    4. Aggregate by ingredient_id

    Returns:
        Dict mapping ingredient_id to aggregated inventory data
    """
    logger.info("[AGGREGATE] Starting inventory aggregation")
    items_with_products = await get_all_items_with_products(db)
    logger.info(f"[AGGREGATE] Found {len(items_with_products)} items with products")
    inventory_map: dict[UUID, InventoryIngredient] = {}

    for entry in items_with_products:
        item = entry["item"]
        product = entry["product"]

        if not product or not product.name:
            logger.warning(f"[AGGREGATE] Skipping item {item.id} - no product name")
            continue

        logger.info(f"[AGGREGATE] Processing product: '{product.name}' (qty: {item.qty} {item.unit})")

        # Try to map product to ingredient via alias
        alias = await get_alias_by_text(db, product.name)

        if not alias:
            logger.warning(f"[AGGREGATE] No alias found for product: '{product.name}'")
            continue

        logger.info(f"[AGGREGATE] Found alias for '{product.name}' → ingredient_id: {alias.ingredient_id}")

        ingredient = await get_ingredient_by_id(db, alias.ingredient_id)
        if not ingredient:
            logger.warning(f"[AGGREGATE] Ingredient not found for id: {alias.ingredient_id}")
            continue

        logger.info(f"[AGGREGATE] Ingredient name: '{ingredient.name}'")

        # Item.qty is already in base units — use directly
        total_qty = item.qty
        base_unit = item.unit

        # Aggregate by ingredient
        ingredient_id = ingredient.id

        if ingredient_id in inventory_map:
            existing = inventory_map[ingredient_id]

            if existing.base_unit == base_unit:
                existing.total_quantity += total_qty
                existing.product_references.append({
                    "product_name": product.name,
                    "quantity": total_qty,
                    "unit": base_unit
                })
                logger.info(f"[AGGREGATE] Added to existing - new total: {existing.total_quantity} {existing.base_unit}")
            else:
                logger.warning(f"[AGGREGATE] Unit mismatch: {existing.base_unit} vs {base_unit}")
        else:
            inventory_map[ingredient_id] = InventoryIngredient(
                ingredient_id=ingredient_id,
                ingredient_name=ingredient.name,
                total_quantity=total_qty,
                base_unit=base_unit,
                product_references=[{
                    "product_name": product.name,
                    "quantity": total_qty,
                    "unit": base_unit
                }]
            )
            logger.info(f"[AGGREGATE] Created new inventory entry for '{ingredient.name}'")

    logger.info(f"[AGGREGATE] Complete: Aggregated inventory for {len(inventory_map)} ingredients")
    for _, inv_data in inventory_map.items():
        logger.info(f"[AGGREGATE] - {inv_data.ingredient_name}: {inv_data.total_quantity} {inv_data.base_unit}")
    return inventory_map


async def match_recipe_to_inventory(
    db: AsyncSession,
    recipe: Recipe,
    inventory: dict[UUID, InventoryIngredient]
) -> RecipeMatchResult:
    """
    Match a single recipe against available inventory.

    Returns:
        RecipeMatchResult with availability details and substitution suggestions
    """
    logger.info(f"[MATCH] Matching recipe '{recipe.title}'")
    recipe_ingredients = await get_recipe_ingredients(db, recipe.id)
    logger.info(f"[MATCH] Recipe has {len(recipe_ingredients)} ingredients")

    ingredient_availability = []
    missing_ingredients = []
    suggested_substitutions = []
    total_ingredients = len(recipe_ingredients)
    available_count = 0

    for recipe_ing in recipe_ingredients:
        ingredient = await get_ingredient_by_id(db, recipe_ing.canonical_ingredient_id)
        if not ingredient:
            logger.warning(f"[MATCH] Ingredient not found for id: {recipe_ing.canonical_ingredient_id}")
            continue

        logger.info(f"[MATCH] Checking ingredient '{ingredient.name}': need {recipe_ing.quantity} {recipe_ing.unit}")

        # Convert recipe requirement to base unit
        required_conversion = await convert_to_base_unit(
            recipe_ing.quantity,
            recipe_ing.unit,
            ingredient.name
        )

        logger.info(f"[MATCH] Required (converted): {required_conversion['quantity']} {required_conversion['base_unit']}")

        # Check if ingredient is in inventory
        if recipe_ing.canonical_ingredient_id in inventory:
            logger.info(f"[MATCH] Ingredient '{ingredient.name}' found in inventory")
            inv_data = inventory[recipe_ing.canonical_ingredient_id]

            if inv_data.base_unit == required_conversion["base_unit"]:
                is_sufficient = inv_data.total_quantity >= required_conversion["quantity"]

                ingredient_availability.append(IngredientAvailability(
                    ingredient_id=ingredient.id,
                    ingredient_name=ingredient.name,
                    required_quantity=required_conversion["quantity"],
                    available_quantity=inv_data.total_quantity,
                    unit=required_conversion["base_unit"],
                    is_sufficient=is_sufficient
                ))

                if is_sufficient:
                    available_count += 1
                else:
                    missing_ingredients.append(ingredient.name)
            else:
                # Incompatible units - treat as missing
                ingredient_availability.append(IngredientAvailability(
                    ingredient_id=ingredient.id,
                    ingredient_name=ingredient.name,
                    required_quantity=required_conversion["quantity"],
                    available_quantity=0.0,
                    unit=required_conversion["base_unit"],
                    is_sufficient=False
                ))
                missing_ingredients.append(ingredient.name)
        else:
            # Ingredient not in inventory - check for substitutions
            logger.warning(f"[MATCH] Ingredient '{ingredient.name}' NOT in inventory")
            substitution = await find_substitution_for_ingredient(
                db,
                recipe_ing.canonical_ingredient_id,
                inventory,
                required_quantity=required_conversion["quantity"],
                required_unit=required_conversion["base_unit"],
            )

            if substitution:
                # Substitution available counts as covered
                suggested_substitutions.append(substitution)
                available_count += 1
            else:
                missing_ingredients.append(ingredient.name)

            ingredient_availability.append(IngredientAvailability(
                ingredient_id=ingredient.id,
                ingredient_name=ingredient.name,
                required_quantity=required_conversion["quantity"],
                available_quantity=0.0,
                unit=required_conversion["base_unit"],
                is_sufficient=substitution is not None
            ))

    # availability_percent counts substitutions as covered
    availability_percent = (available_count / total_ingredients * 100) if total_ingredients > 0 else 0

    if availability_percent == 100:
        match_type = "unlocked"
    elif availability_percent >= 70:
        match_type = "almost"
    else:
        match_type = "locked"

    logger.info(f"[MATCH] Result: {match_type} ({availability_percent:.0f}%), missing: {missing_ingredients}")

    return RecipeMatchResult(
        recipe_id=recipe.id,
        recipe_title=recipe.title,
        recipe_description=recipe.description,
        recipe_image_url=recipe.image_url,
        match_type=match_type,
        availability_percent=availability_percent,
        ingredient_availability=ingredient_availability,
        missing_ingredients=missing_ingredients,
        suggested_substitutions=suggested_substitutions
    )


async def find_substitution_for_ingredient(
    db: AsyncSession,
    ingredient_id: UUID,
    inventory: dict[UUID, InventoryIngredient],
    required_quantity: float = 0.0,
    required_unit: str = "g",
) -> SubstitutionSuggestion | None:
    """
    Find best substitution for a missing ingredient, ranked by inventory availability.

    Ranking priority:
    1. Has sufficient quantity in inventory (adjusted by ratio)
    2. Highest quality_score

    Only considers substitutes with quality_score >= 5 that are in inventory.
    """
    substitutions = await get_substitutions_for_ingredient(db, ingredient_id)

    # Filter to viable candidates: quality >= 5 and present in inventory
    candidates = []
    for sub in substitutions:
        if sub.quality_score < 5:
            continue
        if sub.substitute_ingredient_id not in inventory:
            continue

        inv_data = inventory[sub.substitute_ingredient_id]
        needed = required_quantity * sub.ratio
        has_enough = (
            inv_data.base_unit == required_unit
            and inv_data.total_quantity >= needed
        ) if required_quantity > 0 else False

        candidates.append((sub, has_enough))

    if not candidates:
        return None

    # Sort: sufficient quantity first, then by quality_score descending
    candidates.sort(key=lambda c: (c[1], c[0].quality_score), reverse=True)
    best_sub, _ = candidates[0]

    substitute_ing = await get_ingredient_by_id(db, best_sub.substitute_ingredient_id)
    original_ing = await get_ingredient_by_id(db, ingredient_id)

    if not substitute_ing or not original_ing:
        return None

    return SubstitutionSuggestion(
        original_ingredient_id=ingredient_id,
        original_ingredient_name=original_ing.name,
        substitute_ingredient_id=best_sub.substitute_ingredient_id,
        substitute_ingredient_name=substitute_ing.name,
        ratio=best_sub.ratio,
        quality_score=best_sub.quality_score,
        notes=best_sub.notes,
    )


async def match_all_recipes(db: AsyncSession) -> RecipeMatchResponse:
    """
    Match all recipes against current inventory.

    Returns:
        Categorized results: can_make_now, missing_one, missing_few, with_substitutions
    """
    inventory = await aggregate_inventory_by_ingredient(db)
    recipes = await get_all_recipes(db)

    all_matches = []
    for recipe in recipes:
        match_result = await match_recipe_to_inventory(db, recipe, inventory)
        all_matches.append(match_result)

    unlocked = []
    almost = []
    locked = []

    for match in all_matches:
        if match.match_type == "unlocked":
            unlocked.append(match)
        elif match.match_type == "almost":
            almost.append(match)
        else:
            locked.append(match)

    logger.info(f"Recipe matching complete: {len(unlocked)} unlocked, "
                f"{len(almost)} almost, {len(locked)} locked")

    return RecipeMatchResponse(
        unlocked=unlocked,
        almost=almost,
        locked=locked,
        total_recipes_checked=len(recipes)
    )
