import asyncio
import os
import httpx
from recipe_scrapers import scrape_me, scrape_html
from typing import Optional
import logging

logger = logging.getLogger(__name__)

FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL", "http://flaresolverr:8191/v1")


async def _fetch_via_flaresolverr(url: str) -> Optional[str]:
    """Fetch page HTML through FlareSolverr to bypass Cloudflare."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                FLARESOLVERR_URL,
                json={"cmd": "request.get", "url": url, "maxTimeout": 30000},
            )
            data = resp.json()
            if data.get("status") == "ok":
                return data["solution"]["response"]
    except Exception as e:
        logger.warning(f"FlareSolverr failed for {url}: {e}")
    return None


async def parse_recipe_from_url(url: str) -> Optional[dict]:
    """
    Parse recipe from URL using recipe-scrapers library.
    Tries a direct fetch first; falls back to FlareSolverr if blocked.
    """
    try:
        loop = asyncio.get_event_loop()
        scraper = await loop.run_in_executor(None, lambda: scrape_me(url, supported_only=False))
        return _extract(scraper, url)
    except Exception as e:
        logger.info(f"Direct scrape failed for {url} ({e}), trying FlareSolverr")

    html = await _fetch_via_flaresolverr(url)
    if html:
        try:
            loop = asyncio.get_event_loop()
            scraper = await loop.run_in_executor(None, lambda: scrape_html(html=html, org_url=url, supported_only=False))
            return _extract(scraper, url)
        except Exception as e:
            logger.error(f"FlareSolverr HTML parse failed for {url}: {e}")

    return None


def _extract(scraper, url: str) -> dict:
    """Extract recipe data from a scraper instance."""
    return {
        "title": scraper.title(),
        "description": scraper.description() if hasattr(scraper, 'description') else None,
        "ingredients": scraper.ingredients(),
        "instructions": scraper.instructions_list() or [scraper.instructions()],
        "source_url": url,
        "image_url": scraper.image() if hasattr(scraper, 'image') else None,
        "yields": scraper.yields() if hasattr(scraper, 'yields') else None,
        "total_time": scraper.total_time() if hasattr(scraper, 'total_time') else None,
    }


def normalize_product_name(product_name: str) -> str:
    """
    Normalize a scanned product name for ingredient matching.

    Lighter touch than normalize_ingredient_text — only strips brand/quality
    qualifiers that are never part of an ingredient's identity. Preserves
    descriptor words like "whole", "grain", "light", "dark", "plain" that
    form compound ingredient names (e.g. "whole grain flour", "dark chocolate").

    Example: "Organic Whole Grain Flour" -> "whole grain flour"
    """
    text = product_name.lower().strip()

    remove_words = {
        # Brand/quality qualifiers
        'organic', 'natural', 'pure', 'premium', 'fancy', 'select', 'choice',
        'grade', 'quality', 'unbleached', 'enriched',
        # Certifications
        'certified', 'non-gmo', 'gmo', 'fair', 'trade', 'kosher', 'halal',
        # Store brand noise
        'brand', 'original', 'classic',
    }

    words = text.split()
    filtered = [w for w in words if w not in remove_words]
    normalized = ' '.join(filtered).strip()
    logger.info(f"[NORMALIZE_PRODUCT] '{product_name}' -> '{normalized}'")
    return normalized


def normalize_ingredient_text(ingredient_text: str) -> str:
    """
    Normalize ingredient text for matching.
    Removes quantities, units, and extra words to get canonical ingredient.

    Example: "2 cups all-purpose flour" -> "flour"
    """
    text = ingredient_text.lower().strip()

    # Strip leading preparation phrases that word-level filtering can't catch
    phrase_prefixes = [
        "juice and zest of ",
        "juice of ",
        "zest of ",
        "optional variation: ",
        "optional: ",
    ]
    for prefix in phrase_prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break

    # Remove common quantity words, units, and descriptive modifiers
    remove_words = {
        # Units
        'cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
        'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb', 'lbs', 'gram', 'grams', 'g',
        'kilogram', 'kilograms', 'kg', 'liter', 'liters', 'l', 'milliliter', 'milliliters', 'ml',
        'pinch', 'dash', 'handful', 'slice', 'slices', 'piece', 'pieces', 'pcs',
        # Preparation methods
        'chopped', 'diced', 'minced', 'sliced', 'fresh', 'dried', 'ground', 'crushed', 'grated',
        'shredded', 'melted', 'softened', 'beaten', 'whisked', 'toasted', 'roasted',
        # Plant part descriptors (e.g. "cilantro leaves" → "cilantro")
        'leaves', 'leaf', 'stalks', 'stalk', 'sprig', 'sprigs', 'florets', 'floret',
        # Size descriptors
        'large', 'medium', 'small', 'whole', 'half', 'quarter', 'mini', 'extra', 'jumbo',
        # Range/connector words (e.g. "1 to 2 jalapeños" → "jalapeños")
        'to',
        # Quality descriptors
        'pure', 'organic', 'natural', 'raw', 'unbleached', 'free', 'range', 'cage',
        'grade', 'quality', 'premium', 'fancy', 'select', 'choice',
        # Common adjectives
        'all-purpose', 'purpose', 'all', 'light', 'dark', 'unsalted', 'salted', 'sweetened',
        'unsweetened', 'plain', 'regular', 'low', 'fat', 'sodium', 'reduced',
        # Optional/variation markers that slip through scraping
        'optional', 'variation',
    }

    words = text.split()
    filtered = []

    for word in words:
        # Skip numbers and fractions
        if word.replace('.', '').replace('/', '').isdigit():
            continue
        # Skip common words
        if word in remove_words:
            continue
        # Skip parenthetical notes
        if '(' in word or ')' in word:
            continue
        filtered.append(word)

    normalized = ' '.join(filtered).strip()
    logger.info(f"[NORMALIZE] '{ingredient_text}' -> '{normalized}'")
    return normalized
