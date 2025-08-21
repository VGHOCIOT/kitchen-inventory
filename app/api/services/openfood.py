import httpx

async def lookup_barcode(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                return {
                    "name": product.get("product_name"),
                    "brands": arrayify(product.get("brands")),
                    "categories": arrayify(product.get("categories"))
                }
    return None

def arrayify(arg: str | None) -> list[str]:
    if not arg:
        return []
    return [s.strip() for s in arg.split(",")]