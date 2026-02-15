import httpx
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")


async def parse_ingredient(ingredient_text: str) -> Optional[dict]:
    """
    Parse ingredient text using Spoonacular API.

    Returns:
        {
            "name": "butter",
            "amount": 2.0,
            "unit": "tablespoons",
            "original": "2 tablespoons butter",
            "metric_amount": 28.0,  # Optional: if measures.metric exists
            "metric_unit": "g"       # Optional: if measures.metric exists
        }
    """
    if not SPOONACULAR_API_KEY:
        return None

    url = "https://api.spoonacular.com/recipes/parseIngredients"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                params={"apiKey": SPOONACULAR_API_KEY},
                data={
                    "ingredientList": ingredient_text,
                    "servings": 1,
                    "includeNutrition": False
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    parsed = data[0]
                    logger.info(f"[SPOON] Raw parsed data for '{ingredient_text}': {parsed}")

                    result = {
                        "name": parsed.get("name", ""),
                        "amount": parsed.get("amount", 1.0),
                        "unit": parsed.get("unit", "unit"),
                        "original": parsed.get("original", ingredient_text)
                    }

                    # Extract metric weight data if available
                    measures = parsed.get("measures", {})
                    logger.info(f"[SPOON] Measures data: {measures}")
                    metric = measures.get("metric", {})
                    logger.info(f"[SPOON] Metric data: {metric}")

                    if metric and metric.get("amount"):
                        result["metric_amount"] = metric.get("amount")
                        result["metric_unit"] = metric.get("unitShort", metric.get("unitLong", ""))
                        logger.info(f"[SPOON] ✓ Extracted metric: {result['metric_amount']} {result['metric_unit']} for '{result['name']}'")
                    else:
                        logger.info(f"[SPOON] ✗ No metric data available for '{result['name']}'")

                    return result
        except Exception as e:
            logger.error(f"[SPOON] API error: {e}")
            return None

    return None


async def parse_ingredients_batch(ingredient_list: list[str]) -> list[dict]:
    """
    Parse multiple ingredients in one API call.

    Args:
        ingredient_list: List of ingredient strings

    Returns:
        List of parsed ingredient dicts with optional metric data
    """
    if not SPOONACULAR_API_KEY:
        # Fallback: return simple parsing
        return [{"name": ing, "amount": 1.0, "unit": "unit", "original": ing} for ing in ingredient_list]

    url = "https://api.spoonacular.com/recipes/parseIngredients"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                params={"apiKey": SPOONACULAR_API_KEY},
                data={
                    "ingredientList": "\n".join(ingredient_list),
                    "servings": 1,
                    "includeNutrition": False
                },
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"[SPOON] Batch parsing {len(data)} ingredients")
                results = []
                for parsed in data:
                    logger.info(f"[SPOON] Batch raw data: {parsed}")

                    result = {
                        "name": parsed.get("name", ""),
                        "amount": parsed.get("amount", 1.0),
                        "unit": parsed.get("unit", "unit"),
                        "original": parsed.get("original", "")
                    }

                    # Extract metric weight data if available
                    measures = parsed.get("measures", {})
                    logger.info(f"[SPOON] Batch measures: {measures}")
                    metric = measures.get("metric", {})
                    logger.info(f"[SPOON] Batch metric: {metric}")

                    if metric and metric.get("amount"):
                        result["metric_amount"] = metric.get("amount")
                        result["metric_unit"] = metric.get("unitShort", metric.get("unitLong", ""))
                        logger.info(f"[SPOON] ✓ Batch extracted metric: {result['metric_amount']} {result['metric_unit']} for '{result['name']}'")
                    else:
                        logger.info(f"[SPOON] ✗ Batch no metric data for '{result['name']}'")

                    results.append(result)
                return results
            else:
                logger.warning(f"Spoonacular returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Spoonacular API error: {e}")

    # Fallback on error
    return [{"name": ing, "amount": 1.0, "unit": "unit", "original": ing} for ing in ingredient_list]
