import httpx
import re

async def lookup_barcode(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                quantity_data = parse_quantity(product)
                return {
                    "name": product.get("product_name"),
                    "brands": arrayify(product.get("brands")),
                    "categories": arrayify(product.get("categories")),
                    "package_quantity": quantity_data.get("quantity"),
                    "package_unit": quantity_data.get("unit")
                }
    return None

def arrayify(arg: str | None) -> list[str]:
    if not arg:
        return []
    return [s.strip() for s in arg.split(",")]

def parse_quantity(product: dict) -> dict:
    """Extract package quantity and unit from OpenFoodFacts product data"""
    # Try structured fields first
    if product.get("product_quantity") and product.get("product_quantity_unit"):
        return {
            "quantity": float(product["product_quantity"]),
            "unit": standardize_unit(product["product_quantity_unit"])
        }

    # Fall back to parsing quantity string (e.g., "250 g", "1 L")
    quantity_str = product.get("quantity", "")
    if quantity_str:
        match = re.match(r"([\d.,]+)\s*([a-zA-Z]+)", quantity_str)
        if match:
            qty = match.group(1).replace(",", ".")
            unit = match.group(2)
            return {
                "quantity": float(qty),
                "unit": standardize_unit(unit)
            }

    return {"quantity": None, "unit": None}

def standardize_unit(unit: str) -> str:
    """Standardize unit names to common formats"""
    unit = unit.lower().strip()

    # Weight conversions
    if unit in ["g", "gr", "gram", "grams"]:
        return "g"
    if unit in ["kg", "kilo", "kilogram", "kilograms"]:
        return "kg"

    # Volume conversions
    if unit in ["ml", "milliliter", "milliliters", "millilitre", "millilitres"]:
        return "ml"
    if unit in ["l", "liter", "liters", "litre", "litres"]:
        return "l"
    if unit in ["cl", "centiliter", "centiliters"]:
        return "cl"

    # Count/discrete units
    if unit in ["unit", "units", "piece", "pieces", "item", "items"]:
        return "unit"

    return unit