"""
Unit conversion service for recipe ingredients.

Handles conversion between different measurement units with ingredient-specific
density mappings for accurate volume-to-weight conversions.
"""

from typing import Optional


def standardize_unit(unit: str) -> str:
    """Standardize unit names to common formats"""
    # Handle None or blank units early (discrete/count-based)
    if not unit:
        return "unit"

    unit = unit.lower().strip()

    # Empty/blank units are discrete (count-based) - e.g., "2 eggs" with no unit
    if unit == "":
        return "unit"

    # Weight conversions
    if unit in ["g", "gr", "gram", "grams"]:
        return "g"
    if unit in ["kg", "kilo", "kilogram", "kilograms"]:
        return "kg"
    if unit in ["oz", "ounce", "ounces"]:
        return "oz"
    if unit in ["lb", "lbs", "pound", "pounds"]:
        return "lb"

    # Volume conversions
    if unit in ["ml", "milliliter", "milliliters", "millilitre", "millilitres"]:
        return "ml"
    if unit in ["l", "liter", "liters", "litre", "litres"]:
        return "l"
    if unit in ["cl", "centiliter", "centiliters"]:
        return "cl"
    if unit in ["cup", "cups", "c"]:
        return "cup"
    if unit in ["tbsp", "tablespoon", "tablespoons", "tbs", "T"]:
        return "tbsp"
    if unit in ["tsp", "teaspoon", "teaspoons", "t"]:
        return "tsp"
    if unit in ["fl oz", "floz", "fluid ounce", "fluid ounces"]:
        return "fl oz"
    if unit in ["pint", "pints", "pt"]:
        return "pint"
    if unit in ["quart", "quarts", "qt"]:
        return "quart"
    if unit in ["gal", "gallon", "gallons"]:
        return "gallon"

    # Count/discrete units - all standardize to "unit"
    if unit in ["unit", "units", "piece", "pieces", "item", "items", "pcs", "pc", "whole", "count",
                "clove", "cloves", "packet", "packets", "serving", "servings", "bag", "bags",
                "can", "cans", "jar", "jars", "bottle", "bottles", "box", "boxes",
                "small", "medium", "large", "head", "heads", "bunch", "bunches",
                "slice", "slices", "stalk", "stalks", "sprig", "sprigs", "leaf", "leaves"]:
        return "unit"

    # Dozen is special - keep it separate for 12x conversion
    if unit in ["dozen", "doz"]:
        return "dozen"

    return unit


# Dry ingredients: grams per cup
DRY_INGREDIENT_DENSITIES = {
    "flour": 120,
    "all-purpose flour": 120,
    "bread flour": 127,
    "cake flour": 114,
    "whole wheat flour": 120,
    "sugar": 200,
    "white sugar": 200,
    "granulated sugar": 200,
    "brown sugar": 220,
    "powdered sugar": 120,
    "confectioners sugar": 120,
    "butter": 227,
    "cocoa powder": 85,
    "oats": 90,
    "rice": 185,
    "salt": 292,
    "baking soda": 220,
    "baking powder": 192,
}

# Liquid ingredients: ml per cup
LIQUID_INGREDIENT_DENSITIES = {
    "milk": 240,
    "water": 240,
    "oil": 240,
    "vegetable oil": 240,
    "olive oil": 216,
    "honey": 340,
    "maple syrup": 312,
    "vanilla extract": 240,
}

# Weight unit conversions to grams
WEIGHT_TO_GRAMS = {
    "g": 1.0,
    "kg": 1000.0,
    "oz": 28.35,
    "lb": 453.59,
    "lbs": 453.59,
}

# Volume unit conversions to milliliters
VOLUME_TO_ML = {
    "ml": 1.0,
    "l": 1000.0,
    "cl": 10.0,
    "cup": 240.0,
    "cups": 240.0,
    "tbsp": 14.79,
    "tablespoon": 14.79,
    "tablespoons": 14.79,
    "tsp": 4.93,
    "teaspoon": 4.93,
    "teaspoons": 4.93,
    "fl oz": 29.57,
    "floz": 29.57,
    "pint": 473.18,
    "quart": 946.35,
    "gallon": 3785.41,
}

# Discrete units (count-based) - after standardization
# Note: All discrete units get standardized to "unit" except "dozen" which converts to 12 units
DISCRETE_UNITS = {"unit", "dozen"}

# Default densities for unknown ingredients
DEFAULT_DRY_DENSITY = 150  # g/cup - reasonable average for dry ingredients
DEFAULT_LIQUID_DENSITY = 240  # ml/cup - standard for liquids

# Keywords that indicate an ingredient is a liquid
LIQUID_KEYWORDS = {
    "oil", "milk", "water", "juice", "broth", "stock", "sauce", "vinegar",
    "wine", "beer", "liquor", "cream", "yogurt", "buttermilk", "extract",
    "syrup", "honey", "molasses", "marinade", "dressing", "gravy"
}


def is_likely_liquid(ingredient_name: Optional[str]) -> bool:
    """
    Determine if an ingredient is likely a liquid based on its name.

    Args:
        ingredient_name: Name of the ingredient

    Returns:
        True if ingredient appears to be a liquid
    """
    if not ingredient_name:
        return False

    name_lower = ingredient_name.lower()
    return any(keyword in name_lower for keyword in LIQUID_KEYWORDS)


async def convert_to_base_unit(
    quantity: float,
    unit: str,
    ingredient_name: Optional[str] = None
) -> dict:
    """
    Convert quantity to base unit (grams, ml, or unit).

    Args:
        quantity: Numeric amount
        unit: Unit of measurement (empty string treated as discrete "unit")
        ingredient_name: Optional ingredient name for density-based conversions

    Returns:
        {
            "quantity": float,             # Converted quantity
            "base_unit": "g" | "ml" | "unit",  # Target unit
            "conversion_confidence": "high" | "medium" | "low"
        }
    """
    # Handle blank/empty units (discrete items like "2 eggs")
    if not unit or unit.strip() == "":
        return {
            "quantity": quantity,
            "base_unit": "unit",
            "conversion_confidence": "high"
        }

    # Standardize the unit first
    unit = standardize_unit(unit.lower().strip())

    # Normalize ingredient name if provided
    ingredient_norm = ingredient_name.lower().strip() if ingredient_name else None

    # Handle discrete units (no conversion)
    if unit in DISCRETE_UNITS:
        # Special case: dozen → 12 units
        if unit == "dozen":
            return {
                "quantity": quantity * 12,
                "base_unit": "unit",
                "conversion_confidence": "high"
            }
        return {
            "quantity": quantity,
            "base_unit": "unit",
            "conversion_confidence": "high"
        }

    # Try weight conversion
    if unit in WEIGHT_TO_GRAMS:
        return {
            "quantity": quantity * WEIGHT_TO_GRAMS[unit],
            "base_unit": "g",
            "conversion_confidence": "high"
        }

    # Try volume conversion
    if unit in VOLUME_TO_ML:
        ml_value = quantity * VOLUME_TO_ML[unit]

        # Strategy: Check specific density table first, then use heuristics + defaults

        # 1. Check if we have a specific dry ingredient density
        if ingredient_norm and ingredient_norm in DRY_INGREDIENT_DENSITIES:
            cups = ml_value / 240.0
            grams = cups * DRY_INGREDIENT_DENSITIES[ingredient_norm]
            return {
                "quantity": grams,
                "base_unit": "g",
                "conversion_confidence": "high"
            }

        # 2. Check if we have a specific liquid ingredient density
        if ingredient_norm and ingredient_norm in LIQUID_INGREDIENT_DENSITIES:
            return {
                "quantity": ml_value,
                "base_unit": "ml",
                "conversion_confidence": "high"
            }

        # 3. Use heuristics to determine if liquid or dry, then apply defaults
        if ingredient_name:
            if is_likely_liquid(ingredient_name):
                # Liquid ingredient - keep as ml
                return {
                    "quantity": ml_value,
                    "base_unit": "ml",
                    "conversion_confidence": "medium"
                }
            else:
                # Likely dry ingredient - convert to grams using default density
                cups = ml_value / 240.0
                grams = cups * DEFAULT_DRY_DENSITY
                return {
                    "quantity": grams,
                    "base_unit": "g",
                    "conversion_confidence": "medium"
                }

        # 4. No ingredient name provided - keep as ml with low confidence
        return {
            "quantity": ml_value,
            "base_unit": "ml",
            "conversion_confidence": "low"
        }

    # Unit not recognized - return as-is with low confidence
    return {
        "quantity": quantity,
        "base_unit": unit,  # Keep original unit
        "conversion_confidence": "low"
    }


async def can_convert_units(unit_a: str, unit_b: str) -> bool:
    """
    Check if two units can be converted between each other.

    Args:
        unit_a: First unit (empty string treated as discrete "unit")
        unit_b: Second unit (empty string treated as discrete "unit")

    Returns:
        True if units are convertible (same dimension)
    """
    # Handle blank units
    unit_a = unit_a.strip() if unit_a else ""
    unit_b = unit_b.strip() if unit_b else ""

    unit_a = standardize_unit(unit_a.lower() if unit_a else "")
    unit_b = standardize_unit(unit_b.lower() if unit_b else "")

    # Same unit
    if unit_a == unit_b:
        return True

    # Both weight units
    if unit_a in WEIGHT_TO_GRAMS and unit_b in WEIGHT_TO_GRAMS:
        return True

    # Both volume units
    if unit_a in VOLUME_TO_ML and unit_b in VOLUME_TO_ML:
        return True

    # Both discrete units
    if unit_a in DISCRETE_UNITS and unit_b in DISCRETE_UNITS:
        return True

    return False


async def are_compatible_units(unit_a: str, unit_b: str) -> bool:
    """
    Check if units represent the same dimension (weight, volume, or count).
    Alias for can_convert_units for clarity.

    Args:
        unit_a: First unit
        unit_b: Second unit

    Returns:
        True if units are compatible
    """
    return await can_convert_units(unit_a, unit_b)


def get_unit_dimension(unit: str) -> str:
    """
    Get the dimension of a unit (weight, volume, or count).

    Args:
        unit: Unit to check (empty string treated as count)

    Returns:
        "weight", "volume", "count", or "unknown"
    """
    # Handle blank units
    if not unit or unit.strip() == "":
        return "count"

    unit = standardize_unit(unit.lower().strip())

    if unit in WEIGHT_TO_GRAMS:
        return "weight"
    if unit in VOLUME_TO_ML:
        return "volume"
    if unit in DISCRETE_UNITS:
        return "count"

    return "unknown"
