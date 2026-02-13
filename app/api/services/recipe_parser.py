import asyncio
from recipe_scrapers import scrape_me
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def parse_recipe_from_url(url: str) -> Optional[dict]:
    """
    Parse recipe from URL using recipe-scrapers library.
    Runs in executor to avoid blocking async event loop.
    """
    try:
        # Run the synchronous scraper in a thread pool
        loop = asyncio.get_event_loop()
        scraper = await loop.run_in_executor(None, scrape_me, url)

        # Extract recipe data
        return {
            "title": scraper.title(),
            "ingredients": scraper.ingredients(),
            "instructions": scraper.instructions_list() or [scraper.instructions()],
            "source_url": url,
            "image_url": scraper.image() if hasattr(scraper, 'image') else None,
            "yields": scraper.yields() if hasattr(scraper, 'yields') else None,
            "total_time": scraper.total_time() if hasattr(scraper, 'total_time') else None,
        }
    except Exception as e:
        logger.error(f"Failed to parse recipe from {url}: {e}")
        return None


def normalize_ingredient_text(ingredient_text: str) -> str:
    """
    Normalize ingredient text for matching.
    Removes quantities, units, and extra words to get canonical ingredient.

    Example: "2 cups all-purpose flour" -> "flour"
    """
    # Simple normalization - can be enhanced with Spoonacular later
    text = ingredient_text.lower().strip()

    # Remove common quantity words, units, and descriptive modifiers
    remove_words = [
        # Units
        'cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
        'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb', 'lbs', 'gram', 'grams', 'g',
        'kilogram', 'kilograms', 'kg', 'liter', 'liters', 'l', 'milliliter', 'milliliters', 'ml',
        'pinch', 'dash', 'handful', 'slice', 'slices', 'piece', 'pieces', 'pcs',
        # Preparation methods
        'chopped', 'diced', 'minced', 'sliced', 'fresh', 'dried', 'ground', 'crushed', 'grated',
        'shredded', 'melted', 'softened', 'beaten', 'whisked', 'toasted', 'roasted',
        # Size descriptors
        'large', 'medium', 'small', 'whole', 'half', 'quarter', 'mini', 'extra', 'jumbo',
        # Quality descriptors
        'pure', 'organic', 'natural', 'raw', 'unbleached', 'free', 'range', 'cage',
        'grade', 'quality', 'premium', 'fancy', 'select', 'choice',
        # Common adjectives
        'all-purpose', 'purpose', 'all', 'light', 'dark', 'unsalted', 'salted', 'sweetened',
        'unsweetened', 'plain', 'regular', 'low', 'fat', 'sodium', 'reduced'
    ]

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
