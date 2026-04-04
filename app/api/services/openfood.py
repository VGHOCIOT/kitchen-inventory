import httpx
import re
from api.services.unit_converter import standardize_unit
from config.canadian_brands import CANADIAN_GROCERY_BRANDS

async def lookup_barcode(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                quantity_data = parse_quantity(product)
                brands = arrayify(product.get("brands"))
                raw_name = strip_package_size(product.get("product_name") or "")
                if not raw_name:
                    raw_name = _name_from_categories(arrayify(product.get("categories")))
                raw_name = strip_brand_from_name(raw_name, brands)
                return {
                    "name": raw_name,
                    "brands": brands,
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


def strip_brand_from_name(name: str, off_brands: list[str]) -> str:
    """
    Remove brand tokens from a product name so ingredient matching works correctly.
    e.g. "Butterball Turkey Bacon" -> "Turkey Bacon"

    Two sources are combined:
    - off_brands: the `brands` field returned by OpenFoodFacts (unreliable, crowd-sourced)
    - CANADIAN_GROCERY_BRANDS: predefined config list of known Canadian grocery brands

    Each brand is tested as a whole phrase match (word-boundary aware) so that a brand
    like "PC" doesn't strip "PC" from ingredient words mid-string.
    """
    if not name:
        return name

    # Build combined set of brand tokens to try, normalised to lowercase
    brand_tokens: set[str] = set(CANADIAN_GROCERY_BRANDS)
    for b in off_brands:
        brand_tokens.add(b.lower().strip())

    cleaned = name
    for brand in brand_tokens:
        if not brand:
            continue
        # Word-boundary match, case-insensitive, strip surrounding whitespace
        pattern = r'(?i)\b' + re.escape(brand) + r'\b'
        cleaned = re.sub(pattern, '', cleaned).strip()
        # Collapse multiple spaces left behind
        cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()

    return cleaned or name  # fall back to original if we stripped everything


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