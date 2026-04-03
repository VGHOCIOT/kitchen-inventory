import httpx
import re
from api.services.unit_converter import standardize_unit

async def lookup_barcode(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                quantity_data = parse_quantity(product)
                raw_name = strip_package_size(product.get("product_name") or "")
                if not raw_name:
                    raw_name = _name_from_categories(arrayify(product.get("categories")))
                return {
                    "name": raw_name,
                    "brands": arrayify(product.get("brands")),
                    "categories": arrayify(product.get("categories")),
                    "package_quantity": quantity_data.get("quantity"),
                    "package_unit": quantity_data.get("unit")
                }
    return None

def _name_from_categories(categories: list[str]) -> str:
    """
    Derive a product name from OpenFoodFacts categories when the product has no name.
    Picks the last category that isn't a raw taxonomy tag (i.e. doesn't start with 'en:').
    e.g. ["Farming products", "Eggs", "Chicken eggs", "en:large-eggs"] -> "Chicken eggs"
    """
    readable = [c for c in categories if not c.lower().startswith("en:")]
    return readable[-1] if readable else ""


def strip_package_size(name: str) -> str:
    """Remove trailing package size suffixes that OpenFoodFacts appends to product names.
    e.g. 'Beef broth 400 g' -> 'Beef broth', 'Tomato Soup 2x300ml' -> 'Tomato Soup'
    """
    return re.sub(r'\s+\d+[\d.,x\s]*(g|ml|kg|l|oz|lb|cl)\s*$', '', name, flags=re.IGNORECASE).strip()


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