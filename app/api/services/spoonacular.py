import httpx
import os
from typing import Optional


SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")


async def parse_ingredient(ingredient_text: str) -> Optional[dict]:
    """
    Parse ingredient text using Spoonacular API.

    Returns:
        {
            "name": "butter",
            "amount": 2.0,
            "unit": "tablespoons",
            "original": "2 tablespoons butter"
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
                    return {
                        "name": parsed.get("name", ""),
                        "amount": parsed.get("amount", 1.0),
                        "unit": parsed.get("unit", "unit"),
                        "original": parsed.get("original", ingredient_text)
                    }
        except Exception as e:
            print(f"Spoonacular API error: {e}")
            return None

    return None


async def parse_ingredients_batch(ingredient_list: list[str]) -> list[dict]:
    """
    Parse multiple ingredients in one API call.

    Args:
        ingredient_list: List of ingredient strings

    Returns:
        List of parsed ingredient dicts
    """
    if not SPOONACULAR_API_KEY:
        # Fallback: return simple parsing
        return [{"name": ing, "amount": 1.0, "unit": "unit", "original": ing} for ing in ingredient_list]

    url = "https://api.spoonacular.com/recipes/parseIngredients"

    async with httpx.AsyncClient() as client:
        try:
            print(f"[DEBUG] Calling Spoonacular with {len(ingredient_list)} ingredients")
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

            print(f"[DEBUG] Spoonacular response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"[DEBUG] Spoonacular returned {len(data)} results")
                results = []
                for parsed in data:
                    results.append({
                        "name": parsed.get("name", ""),
                        "amount": parsed.get("amount", 1.0),
                        "unit": parsed.get("unit", "unit"),
                        "original": parsed.get("original", "")
                    })
                print(f"[DEBUG] First ingredient parsed: {results[0] if results else 'None'}")
                return results
            else:
                print(f"[DEBUG] Non-200 status code: {response.text}")
        except Exception as e:
            print(f"[DEBUG] Spoonacular batch API error: {e}")

    # Fallback on error
    return [{"name": ing, "amount": 1.0, "unit": "unit", "original": ing} for ing in ingredient_list]
