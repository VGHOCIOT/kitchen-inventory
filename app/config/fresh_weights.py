"""
Manual fresh ingredient weights for common items.

Weights based on typical Canadian grocery sizes (Toronto/No Frills).
Start with your most common items, add more as needed.
"""

# Average weights in grams per unit
# Based on typical Canadian grocery/recipe portions
MANUAL_FRESH_WEIGHTS = {
    # Poultry & Meat
    "chicken breast": 340,  # 1 medium boneless/skinless breast
    "chicken thigh": 150,   # 1 boneless thigh
    "chicken leg": 200,     # 1 drumstick + thigh
    "pork chop": 200,       # 1 medium chop
    "beef steak": 225,      # 1 portion steak

    # Vegetables
    "carrot": 60,           # 1 medium carrot
    "bell pepper": 120,     # 1 medium pepper
    "onion": 150,           # 1 medium onion
    "tomato": 150,          # 1 medium tomato
    "potato": 200,          # 1 medium potato
    "zucchini": 200,        # 1 medium zucchini
    "cucumber": 300,        # 1 medium cucumber
    "broccoli": 150,        # 1 crown/head
    "cauliflower": 500,     # 1 head
    "celery": 40,           # 1 stalk
    "garlic": 5,            # 1 clove

    # Fruits
    "apple": 180,           # 1 medium apple
    "banana": 120,          # 1 medium banana
    "orange": 140,          # 1 medium orange
    "lemon": 58,            # 1 medium lemon
    "lime": 44,             # 1 medium lime
    "avocado": 150,         # 1 medium avocado

    # Eggs & Dairy (if not packaged)
    "egg": 50,              # 1 large egg

    # Add more as needed based on your shopping habits
}


def get_manual_weight(ingredient_name: str) -> float | None:
    """
    Get manual weight for an ingredient.

    Args:
        ingredient_name: Normalized ingredient name

    Returns:
        Weight in grams or None if not in manual table
    """
    # Normalize the lookup (lowercase, strip)
    normalized = ingredient_name.lower().strip()
    return MANUAL_FRESH_WEIGHTS.get(normalized)
