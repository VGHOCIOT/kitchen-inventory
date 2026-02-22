"""
USDA FoodData Central API - FNDDS portion weight lookup.

FNDDS (Food and Nutrient Database for Dietary Studies) was specifically built
to convert food portions into gram amounts. Unlike general FoodData Central
search results, FNDDS food detail records contain a foodPortions array with
entries like "1 medium carrot = 61g".

Free API key: https://fdc.nal.usda.gov/api-key-signup.html
Rate limit: 1,000 requests/hour with key, 30/hour without
"""

import httpx
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

USDA_API_KEY = os.getenv("USDA_API_KEY")
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"


def _extract_unit_weight_from_portions(portions: list, ingredient_name: str) -> Optional[float]:
    """
    Extract per-unit gram weight from FNDDS foodPortions array.

    FNDDS portions look like:
      {"amount": 1.0, "modifier": "medium", "gramWeight": 61.0, "portionDescription": "medium"}
      {"amount": 1.0, "modifier": "large",  "gramWeight": 80.0, "portionDescription": "large"}
      {"amount": 0.5, "modifier": "small",  "gramWeight": 30.0, "portionDescription": "small"}

    Strategy:
    1. Prefer amount=1 with "medium" modifier (most representative)
    2. Fall back to any amount=1 portion
    3. Last resort: normalize first portion by dividing gramWeight / amount

    Args:
        portions: foodPortions array from FNDDS detail response
        ingredient_name: Used for logging only

    Returns:
        Per-unit gram weight, or None if extraction fails
    """
    if not portions:
        return None

    # Filter to portions that have gramWeight
    valid = [p for p in portions if p.get("gramWeight") and p.get("amount")]
    if not valid:
        return None

    # Priority 1: amount=1 with "medium" modifier
    for p in valid:
        modifier = (p.get("modifier") or p.get("portionDescription") or "").lower()
        if float(p["amount"]) == 1.0 and "medium" in modifier:
            weight = float(p["gramWeight"])
            logger.debug(f"[USDA] '{ingredient_name}': medium portion = {weight}g")
            return weight

    # Priority 2: any amount=1 portion (take first = smallest/most common)
    for p in valid:
        if float(p["amount"]) == 1.0:
            weight = float(p["gramWeight"])
            modifier = p.get("modifier") or p.get("portionDescription") or "unknown"
            logger.debug(f"[USDA] '{ingredient_name}': amount=1 portion ({modifier}) = {weight}g")
            return weight

    # Priority 3: normalize first portion by dividing gramWeight by amount
    p = valid[0]
    normalized = float(p["gramWeight"]) / float(p["amount"])
    modifier = p.get("modifier") or p.get("portionDescription") or "unknown"
    logger.debug(f"[USDA] '{ingredient_name}': normalized portion ({modifier}) = {normalized}g")
    return normalized


async def get_average_weight(ingredient_name: str) -> Optional[float]:
    """
    Get per-unit gram weight for an ingredient using USDA FNDDS.

    Two-step lookup:
    1. Search for food → get fdcId of best FNDDS match
    2. Fetch food detail → extract from foodPortions array

    Only runs if USDA_API_KEY is set in .env.

    Args:
        ingredient_name: Normalized ingredient name (e.g., "carrot", "chicken breast")

    Returns:
        Per-unit gram weight, or None if not found
    """
    if not USDA_API_KEY:
        logger.debug("[USDA] API key not set, skipping USDA lookup")
        return None

    try:
        async with httpx.AsyncClient() as client:

            # Step 1: Search for best FNDDS match
            search_response = await client.get(
                f"{USDA_BASE_URL}/foods/search",
                params={
                    "api_key": USDA_API_KEY,
                    "query": ingredient_name,
                    "dataType": "Survey (FNDDS)",  # FNDDS only - has portion weights
                    "pageSize": 3,
                },
                timeout=5.0,
            )

            if search_response.status_code != 200:
                logger.warning(f"[USDA] Search failed ({search_response.status_code}) for '{ingredient_name}'")
                return None

            foods = search_response.json().get("foods", [])
            if not foods:
                logger.debug(f"[USDA] No FNDDS results for '{ingredient_name}'")
                return None

            # Use top result
            fdc_id = foods[0]["fdcId"]
            description = foods[0].get("description", "unknown")
            logger.debug(f"[USDA] Best match for '{ingredient_name}': '{description}' (fdcId={fdc_id})")

            # Step 2: Fetch full food detail to get complete foodPortions
            detail_response = await client.get(
                f"{USDA_BASE_URL}/food/{fdc_id}",
                params={"api_key": USDA_API_KEY},
                timeout=5.0,
            )

            if detail_response.status_code != 200:
                logger.warning(f"[USDA] Detail fetch failed ({detail_response.status_code}) for fdcId={fdc_id}")
                return None

            detail = detail_response.json()
            portions = detail.get("foodPortions", [])

            weight = _extract_unit_weight_from_portions(portions, ingredient_name)
            if weight:
                logger.info(f"[USDA] Found weight for '{ingredient_name}': {weight}g (from '{description}')")
                return weight

            logger.debug(f"[USDA] '{description}' has no usable portion weights for '{ingredient_name}'")
            return None

    except httpx.TimeoutException:
        logger.warning(f"[USDA] Timeout fetching weight for '{ingredient_name}'")
        return None
    except Exception as e:
        logger.error(f"[USDA] Error fetching weight for '{ingredient_name}': {e}")
        return None
