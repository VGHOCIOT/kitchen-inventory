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
from crud.ingredient_alias import get_alias_by_text, create_ingredient_alias

from config.ingredient_aliases import INGREDIENT_ALIAS_SEEDS
from config.fresh_weights import MANUAL_FRESH_WEIGHTS
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


@router.post("/seed-aliases")
async def seed_ingredient_aliases(db: AsyncSession = Depends(get_db)):
    """
    Seed the ingredient alias table with known variations.

    Handles cases plural/singular logic can't resolve automatically:
    - Regional names: scallions → green onion, capsicum → bell pepper
    - Synonyms: cilantro → coriander
    - Modifier variants: boneless skinless chicken breast → chicken breast

    Safe to run multiple times - skips aliases that already exist.
    Creates canonical IngredientReference if it doesn't exist yet.
    """
    created_ingredients = 0
    created_aliases = 0
    skipped = 0

    for canonical_name, aliases in INGREDIENT_ALIAS_SEEDS.items():
        # Find or create the canonical ingredient
        ingredient = await get_ingredient_by_name(db, canonical_name)
        if not ingredient:
            ingredient = await get_ingredient_by_normalized_name(db, canonical_name)
        if not ingredient:
            ingredient = await create_ingredient_reference(
                db, name=canonical_name, normalized_name=canonical_name
            )
            created_ingredients += 1

        # Create each alias if it doesn't already exist
        for alias_text in aliases:
            existing = await get_alias_by_text(db, alias_text)
            if existing:
                skipped += 1
            else:
                await create_ingredient_alias(db, alias=alias_text, ingredient_id=ingredient.id)
                created_aliases += 1

    return {
        "ingredients_created": created_ingredients,
        "aliases_created": created_aliases,
        "aliases_skipped": skipped,
        "message": f"Seeded {created_aliases} aliases across {len(INGREDIENT_ALIAS_SEEDS)} canonical ingredients",
    }


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

def _find_canonical_in_seeds(name: str) -> str | None:
    """
    Reverse-lookup INGREDIENT_ALIAS_SEEDS to find the canonical name for an alias.
    e.g. "scallions" → "green onion", "boneless chicken breast" → "chicken breast"
    """
    for canonical, aliases in INGREDIENT_ALIAS_SEEDS.items():
        if name in aliases:
            return canonical
    return None


def _singularize_candidates(name: str) -> list[str]:
    """
    Generate candidate singular forms in priority order.
    e.g. "carrots" → ["carrot"], "green onions" → ["green onion"],
         "cherries" → ["cherry"], "strawberries" → ["strawberry"]
    """
    candidates = []
    words = name.split()

    if len(words) == 1:
        if name.endswith("ies"):                                        # cherries → cherry
            candidates.append(name[:-3] + "y")
        if name.endswith("oes"):                                        # potatoes → potato
            candidates.append(name[:-2])
        if name.endswith("s") and not name.endswith("ss") and not name.endswith("ies"):  # carrots → carrot
            candidates.append(name[:-1])
    elif len(words) > 1:
        last = words[-1]
        if last.endswith("ies"):
            candidates.append(" ".join(words[:-1] + [last[:-3] + "y"]))
        if last.endswith("oes"):
            candidates.append(" ".join(words[:-1] + [last[:-2]]))
        if last.endswith("s") and not last.endswith("ss") and not last.endswith("ies"):  # green onions → green onion
            candidates.append(" ".join(words[:-1] + [last[:-1]]))

    return candidates


async def _get_or_create_canonical(db: AsyncSession, canonical_name: str):
    """Find or create an IngredientReference for a canonical name."""
    ingredient = await get_ingredient_by_name(db, canonical_name)
    if not ingredient:
        ingredient = await get_ingredient_by_normalized_name(db, canonical_name)
    if not ingredient:
        ingredient = await create_ingredient_reference(
            db, name=canonical_name, normalized_name=canonical_name
        )
    return ingredient


async def find_or_create_ingredient(db: AsyncSession, normalized_name: str):
    """
    Find or create an IngredientReference, always resolving to the canonical form.

    Resolution order (first match wins):
    1. Exact DB match
    2. DB alias lookup
    3. Explicit alias seeds (INGREDIENT_ALIAS_SEEDS) - handles regional/synonym cases
       e.g. "scallions" → canonical "green onion"
    4. Singularize + check manual weights table - handles plurals of known ingredients
       e.g. "carrots" → singularize to "carrot" → in MANUAL_FRESH_WEIGHTS → canonical "carrot"
    5. Singularize + check existing DB ingredient
       e.g. "carrots" → "carrot" already in DB from a previous recipe
    6. Name itself is in manual weights (create canonical as-is)
    7. Create new IngredientReference (unknown ingredient)

    When an alias is resolved (steps 3-5), it's saved to the DB so subsequent
    lookups for the same name skip all this and hit step 2 instantly.
    """
    # 1. Exact DB match
    ingredient = await get_ingredient_by_name(db, normalized_name)
    if ingredient:
        return ingredient

    ingredient = await get_ingredient_by_normalized_name(db, normalized_name)
    if ingredient:
        return ingredient

    # 2. DB alias lookup
    alias = await get_alias_by_text(db, normalized_name)
    if alias:
        return await get_ingredient_by_id(db, alias.ingredient_id)

    # 3. Explicit alias seeds (regional names, synonyms, modifier variants)
    canonical_name = _find_canonical_in_seeds(normalized_name)
    if canonical_name:
        ingredient = await _get_or_create_canonical(db, canonical_name)
        await create_ingredient_alias(db, alias=normalized_name, ingredient_id=ingredient.id)
        return ingredient

    # 4. Singularize + check manual weights (create canonical from weights table)
    for candidate in _singularize_candidates(normalized_name):
        if candidate in MANUAL_FRESH_WEIGHTS:
            ingredient = await _get_or_create_canonical(db, candidate)
            await create_ingredient_alias(db, alias=normalized_name, ingredient_id=ingredient.id)
            return ingredient

    # 5. Singularize + check existing DB ingredient
    for candidate in _singularize_candidates(normalized_name):
        ingredient = await get_ingredient_by_name(db, candidate)
        if not ingredient:
            ingredient = await get_ingredient_by_normalized_name(db, candidate)
        if ingredient:
            await create_ingredient_alias(db, alias=normalized_name, ingredient_id=ingredient.id)
            return ingredient

    # 6. Name itself is a known manual weight - create canonical directly
    if normalized_name in MANUAL_FRESH_WEIGHTS:
        return await create_ingredient_reference(
            db, name=normalized_name, normalized_name=normalized_name
        )

    # 7. Unknown ingredient - create as-is
    return await create_ingredient_reference(
        db, name=normalized_name, normalized_name=normalized_name
    )
