"""
USDA FoodData Central API integration for fetching average ingredient weights.

Free API for food nutrition data including portion sizes.
Get API key: https://fdc.nal.usda.gov/api-key-signup.html
"""

import httpx
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

USDA_API_KEY = os.getenv("USDA_API_KEY")
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"


async def get_average_weight(ingredient_name: str) -> Optional[float]:
    """
    Get average weight in grams for an ingredient from USDA FoodData Central.

    Args:
        ingredient_name: Name of ingredient (e.g., "chicken breast", "carrot")

    Returns:
        Average weight in grams, or None if not found
    """
    if not USDA_API_KEY:
        logger.warning("[USDA] API key not configured, skipping USDA lookup")
        return None

    try:
        async with httpx.AsyncClient() as client:
            # Search for the ingredient
            search_url = f"{USDA_BASE_URL}/foods/search"
            params = {
                "api_key": USDA_API_KEY,
                "query": ingredient_name,
                "dataType": ["Survey (FNDDS)", "Foundation"],  # Most reliable data types
                "pageSize": 1  # Just get the top result
            }

            response = await client.get(search_url, params=params, timeout=10)

            if response.status_code != 200:
                logger.warning(f"[USDA] API returned {response.status_code} for '{ingredient_name}'")
                return None

            data = response.json()
            foods = data.get("foods", [])

            if not foods:
                logger.info(f"[USDA] No results found for '{ingredient_name}'")
                return None

            # Get the first (best match) food item
            food = foods[0]

            # Try to extract portion/serving size in grams
            # USDA data has "servingSize" and "servingSizeUnit"
            serving_size = food.get("servingSize")
            serving_unit = food.get("servingSizeUnit", "").lower()

            if serving_size and serving_unit == "g":
                weight_g = float(serving_size)
                logger.info(f"[USDA] Found weight for '{ingredient_name}': {weight_g}g (from '{food.get('description')}')")
                return weight_g

            # Fallback: Check food portions
            portions = food.get("foodPortions", [])
            for portion in portions:
                if portion.get("gramWeight"):
                    weight_g = float(portion["gramWeight"])
                    logger.info(f"[USDA] Found weight for '{ingredient_name}': {weight_g}g from portion data")
                    return weight_g

            logger.info(f"[USDA] Found '{food.get('description')}' but no weight data available")
            return None

    except Exception as e:
        logger.error(f"[USDA] Error fetching data for '{ingredient_name}': {e}")
        return None
