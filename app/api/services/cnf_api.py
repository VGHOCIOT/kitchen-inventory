"""
Canadian Nutrient File (CNF) API integration for per-unit gram weights.

The CNF is maintained by Health Canada and covers ~5,690 foods with
Canadian-specific fortification levels and Canada-only products.
No API key required. Updated January 2025.

API base: https://food-nutrition.canada.ca/api/canadian-nutrient-file/

The /servingsize/ endpoint returns conversion factors. A conversion factor
multiplied by 100g gives the gram weight for that serving description.
For example: factor=0.61 → 61g per medium carrot.
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

CNF_BASE_URL = "https://food-nutrition.canada.ca/api/canadian-nutrient-file"


def _extract_unit_weight_from_servings(servings: list, ingredient_name: str) -> Optional[float]:
    """
    Extract per-unit gram weight from CNF serving size records.

    CNF serving records look like:
      {"serving_description": "1 medium (7.5 cm long)", "conversion_factor_value": 0.61}
      {"serving_description": "1 large",                "conversion_factor_value": 0.90}
      {"serving_description": "1 cup, chopped",         "conversion_factor_value": 1.28}

    Gram weight = conversion_factor_value * 100

    Strategy:
    1. Prefer descriptions starting with "1 " and containing "medium"
    2. Fall back to any description starting with "1 "
    3. Ignore cup/tablespoon/volume measures (not per-unit)

    Args:
        servings: Array of serving size records from CNF
        ingredient_name: Used for logging only

    Returns:
        Per-unit gram weight, or None
    """
    if not servings:
        return None

    # Volume units to skip - we want count-based portions only
    volume_keywords = ["cup", "tbsp", "tsp", "tablespoon", "teaspoon", "ml", "oz", "fluid"]

    def is_volume(desc: str) -> bool:
        return any(kw in desc.lower() for kw in volume_keywords)

    def conversion_to_grams(record: dict) -> Optional[float]:
        factor = record.get("conversionFactorValue") or record.get("conversion_factor_value")
        if factor:
            return float(factor) * 100
        return None

    # Priority 1: starts with "1 " and contains "medium"
    for s in servings:
        desc = (s.get("servingDescription") or s.get("serving_description") or "").lower()
        if desc.startswith("1 ") and "medium" in desc and not is_volume(desc):
            grams = conversion_to_grams(s)
            if grams:
                logger.debug(f"[CNF] '{ingredient_name}': medium serving '{desc}' = {grams}g")
                return grams

    # Priority 2: starts with "1 " (any non-volume)
    for s in servings:
        desc = (s.get("servingDescription") or s.get("serving_description") or "").lower()
        if desc.startswith("1 ") and not is_volume(desc):
            grams = conversion_to_grams(s)
            if grams:
                logger.debug(f"[CNF] '{ingredient_name}': unit serving '{desc}' = {grams}g")
                return grams

    return None


async def get_average_weight(ingredient_name: str) -> Optional[float]:
    """
    Get per-unit gram weight from the Canadian Nutrient File API.

    Two-step lookup:
    1. Search food list by name → get food_id of best match
    2. Fetch serving sizes for that food → extract per-unit weight

    No API key required. English responses only.

    Args:
        ingredient_name: Normalized ingredient name (e.g., "carrot", "chicken breast")

    Returns:
        Per-unit gram weight, or None if not found
    """
    try:
        async with httpx.AsyncClient() as client:

            # Step 1: Search for food by name
            food_response = await client.get(
                f"{CNF_BASE_URL}/food/",
                params={
                    "lang": "en",
                    "name": ingredient_name,
                },
                timeout=5.0,
            )

            if food_response.status_code != 200:
                logger.warning(f"[CNF] Food search failed ({food_response.status_code}) for '{ingredient_name}'")
                return None

            foods = food_response.json()
            if not foods:
                logger.debug(f"[CNF] No results for '{ingredient_name}'")
                return None

            # Take best match (first result)
            food = foods[0] if isinstance(foods, list) else foods

            # Log raw response keys so we can confirm field names from the actual API
            logger.debug(f"[CNF] Food response keys for '{ingredient_name}': {list(food.keys()) if isinstance(food, dict) else type(food)}")
            logger.debug(f"[CNF] Food response sample: {food}")

            food_id = food.get("foodId") or food.get("food_id") or food.get("FoodID")
            description = food.get("foodDescription") or food.get("food_description") or food.get("FoodDescription") or "unknown"

            if not food_id:
                logger.warning(f"[CNF] Could not extract food_id from response for '{ingredient_name}' - raw keys: {list(food.keys()) if isinstance(food, dict) else food}")
                return None

            logger.debug(f"[CNF] Best match for '{ingredient_name}': '{description}' (id={food_id})")

            # Step 2: Fetch serving sizes for this food
            serving_response = await client.get(
                f"{CNF_BASE_URL}/servingsize/",
                params={
                    "lang": "en",
                    "id": food_id,
                },
                timeout=5.0,
            )

            if serving_response.status_code != 200:
                logger.warning(f"[CNF] Serving size fetch failed ({serving_response.status_code}) for food_id={food_id}")
                return None

            servings = serving_response.json()
            if not servings:
                logger.debug(f"[CNF] No serving sizes for '{description}'")
                return None

            # Log raw serving response so we can confirm field names and structure
            first = servings[0] if isinstance(servings, list) else servings
            logger.debug(f"[CNF] Serving response keys for '{ingredient_name}': {list(first.keys()) if isinstance(first, dict) else type(first)}")
            logger.debug(f"[CNF] Servings sample (first 3): {servings[:3] if isinstance(servings, list) else servings}")

            weight = _extract_unit_weight_from_servings(servings, ingredient_name)
            if weight:
                logger.info(f"[CNF] Found weight for '{ingredient_name}': {weight}g (from '{description}')")
                return weight

            logger.warning(f"[CNF] '{description}' has no usable unit serving sizes for '{ingredient_name}' - all servings: {servings}")
            return None

    except httpx.TimeoutException:
        logger.warning(f"[CNF] Timeout fetching weight for '{ingredient_name}'")
        return None
    except Exception as e:
        logger.error(f"[CNF] Error fetching weight for '{ingredient_name}': {e}")
        return None
