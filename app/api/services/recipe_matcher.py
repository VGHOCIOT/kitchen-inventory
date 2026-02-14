"""
Recipe matching service for inventory-to-recipe matching.

Aggregates inventory by ingredient and determines which recipes can be made
with current items, including substitution suggestions.
"""

from dataclasses import dataclass
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models.ingredient_reference import IngredientReference
from models.recipe import Recipe
from models.recipe_ingredient import RecipeIngredient
from crud.item import get_all_items_with_products
from crud.ingredient_alias import get_alias_by_text
from crud.ingredient_reference import get_ingredient_by_id
from crud.ingredient_substitution import get_substitutions_for_ingredient
from crud.recipe import get_all_recipes
from crud.recipe_ingredient import get_recipe_ingredients
from api.services.unit_converter import convert_to_base_unit, can_convert_units
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

    Process:
    1. Query all Items with ProductReference data
    2. Map each product to its canonical ingredient via IngredientAlias
    3. Calculate total: Item.qty × ProductReference.package_quantity
    4. Convert to base units and aggregate by ingredient_id

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

        # Skip items without product reference data
        if not product or not product.name:
            logger.warning(f"[AGGREGATE] Skipping item {item.id} - no product name")
            continue

        logger.info(f"[AGGREGATE] Processing product: '{product.name}' (qty: {item.qty}, pkg: {product.package_quantity} {product.package_unit})")

        # Try to map product to ingredient via alias
        alias = await get_alias_by_text(db, product.name)

        if not alias:
            # No mapping found - skip this product
            logger.warning(f"[AGGREGATE] ✗ No alias found for product: '{product.name}'")
            continue

        logger.info(f"[AGGREGATE] ✓ Found alias for '{product.name}' → ingredient_id: {alias.ingredient_id}")

        ingredient = await get_ingredient_by_id(db, alias.ingredient_id)
        if not ingredient:
            logger.warning(f"[AGGREGATE] ✗ Ingredient not found for id: {alias.ingredient_id}")
            continue

        logger.info(f"[AGGREGATE] Ingredient name: '{ingredient.name}'")

        # Calculate total quantity for this item
        package_qty = product.package_quantity or 1.0
        package_unit = product.package_unit or "unit"
        total_qty = item.qty * package_qty

        logger.info(f"[AGGREGATE] Total quantity: {total_qty} {package_unit}")

        # Convert to base unit
        conversion = await convert_to_base_unit(
            total_qty,
            package_unit,
            ingredient.name
        )

        logger.info(f"[AGGREGATE] Converted to: {conversion['quantity']} {conversion['base_unit']}")

        # Aggregate by ingredient
        ingredient_id = ingredient.id

        if ingredient_id in inventory_map:
            # Add to existing inventory
            existing = inventory_map[ingredient_id]

            # Only aggregate if units are compatible
            if existing.base_unit == conversion["base_unit"]:
                existing.total_quantity += conversion["quantity"]
                existing.product_references.append({
                    "product_name": product.name,
                    "quantity": total_qty,
                    "unit": package_unit
                })
                logger.info(f"[AGGREGATE] Added to existing - new total: {existing.total_quantity} {existing.base_unit}")
            else:
                logger.warning(f"[AGGREGATE] Unit mismatch: {existing.base_unit} vs {conversion['base_unit']}")
        else:
            # Create new inventory entry
            inventory_map[ingredient_id] = InventoryIngredient(
                ingredient_id=ingredient_id,
                ingredient_name=ingredient.name,
                total_quantity=conversion["quantity"],
                base_unit=conversion["base_unit"],
                product_references=[{
                    "product_name": product.name,
                    "quantity": total_qty,
                    "unit": package_unit
                }]
            )
            logger.info(f"[AGGREGATE] Created new inventory entry for '{ingredient.name}'")

    logger.info(f"[AGGREGATE] Complete: Aggregated inventory for {len(inventory_map)} ingredients")
    for ing_id, inv_data in inventory_map.items():
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
        # Get ingredient details
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
            logger.info(f"[MATCH] ✓ Ingredient '{ingredient.name}' found in inventory")
            inv_data = inventory[recipe_ing.canonical_ingredient_id]

            # Check if units are compatible
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
            logger.warning(f"[MATCH] ✗ Ingredient '{ingredient.name}' NOT in inventory")
            substitution = await find_substitution_for_ingredient(
                db,
                recipe_ing.canonical_ingredient_id,
                inventory
            )

            if substitution:
                suggested_substitutions.append(substitution)

            ingredient_availability.append(IngredientAvailability(
                ingredient_id=ingredient.id,
                ingredient_name=ingredient.name,
                required_quantity=required_conversion["quantity"],
                available_quantity=0.0,
                unit=required_conversion["base_unit"],
                is_sufficient=False
            ))
            missing_ingredients.append(ingredient.name)

    # Calculate availability percentage
    availability_percent = (available_count / total_ingredients * 100) if total_ingredients > 0 else 0

    logger.info(f"[MATCH] Result: {availability_percent:.0f}% available ({available_count}/{total_ingredients}), missing: {missing_ingredients}")

    # Determine match type
    if availability_percent == 100:
        match_type = "exact"
    elif len(suggested_substitutions) > 0:
        match_type = "with_substitutions"
    else:
        match_type = "missing_ingredients"

    return RecipeMatchResult(
        recipe_id=recipe.id,
        recipe_title=recipe.title,
        match_type=match_type,
        availability_percent=availability_percent,
        ingredient_availability=ingredient_availability,
        missing_ingredients=missing_ingredients,
        suggested_substitutions=suggested_substitutions
    )


async def find_substitution_for_ingredient(
    db: AsyncSession,
    ingredient_id: UUID,
    inventory: dict[UUID, InventoryIngredient]
) -> SubstitutionSuggestion | None:
    """
    Find best substitution for a missing ingredient.

    Returns substitution if:
    - Substitute ingredient is in inventory
    - Sufficient quantity available (accounting for ratio)
    - Quality score >= 5
    """
    substitutions = await get_substitutions_for_ingredient(db, ingredient_id)

    for sub in substitutions:
        # Quality threshold
        if sub.quality_score < 5:
            continue

        # Check if substitute is in inventory
        if sub.substitute_ingredient_id in inventory:
            substitute_ing = await get_ingredient_by_id(db, sub.substitute_ingredient_id)
            original_ing = await get_ingredient_by_id(db, ingredient_id)

            if substitute_ing and original_ing:
                return SubstitutionSuggestion(
                    original_ingredient_id=ingredient_id,
                    original_ingredient_name=original_ing.name,
                    substitute_ingredient_id=sub.substitute_ingredient_id,
                    substitute_ingredient_name=substitute_ing.name,
                    ratio=sub.ratio,
                    quality_score=sub.quality_score,
                    notes=sub.notes
                )

    return None


async def match_all_recipes(db: AsyncSession) -> RecipeMatchResponse:
    """
    Match all recipes against current inventory.

    Returns:
        Categorized results: can_make_now, missing_one, missing_few, with_substitutions
    """
    # Build inventory map
    inventory = await aggregate_inventory_by_ingredient(db)

    # Get all recipes
    recipes = await get_all_recipes(db)

    # Match each recipe
    all_matches = []
    for recipe in recipes:
        match_result = await match_recipe_to_inventory(db, recipe, inventory)
        all_matches.append(match_result)

    # Categorize results
    can_make_now = []
    missing_one = []
    missing_few = []
    with_substitutions = []

    for match in all_matches:
        missing_count = len(match.missing_ingredients)

        if match.availability_percent == 100:
            can_make_now.append(match)
        elif missing_count == 1:
            missing_one.append(match)
        elif 2 <= missing_count <= 3:
            missing_few.append(match)
        elif len(match.suggested_substitutions) > 0:
            with_substitutions.append(match)

    logger.info(f"Recipe matching complete: {len(can_make_now)} can make now, "
                f"{len(missing_one)} missing one, {len(missing_few)} missing few, "
                f"{len(with_substitutions)} with substitutions")

    return RecipeMatchResponse(
        can_make_now=can_make_now,
        missing_one=missing_one,
        missing_few=missing_few,
        with_substitutions=with_substitutions,
        total_recipes_checked=len(recipes)
    )
