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
    "pork tenderloin": 450, # 1 portion (usually sold in pairs)
    "beef steak": 225,      # 1 portion steak
    "ground beef": 450,     # 1 lb (common package)
    "ground turkey": 450,   # 1 lb (common package)
    "ground chicken": 450,  # 1 lb (common package)
    "bacon": 450,           # 1 package (usually ~12 slices)
    "sausage": 75,          # 1 link

    # Seafood
    "shrimp": 15,           # 1 large shrimp (peeled)
    "salmon": 170,          # 1 fillet/portion
    "cod": 150,             # 1 fillet/portion
    "tilapia": 120,         # 1 fillet/portion
    "tuna": 150,            # 1 steak/portion

    # Vegetables
    "carrot": 60,           # 1 medium carrot
    "bell pepper": 120,     # 1 medium pepper
    "red bell pepper": 120, # 1 medium pepper
    "green bell pepper": 120, # 1 medium pepper
    "jalapeño": 15,         # 1 pepper
    "serrano pepper": 10,   # 1 pepper
    "poblano pepper": 150,  # 1 medium poblano
    "anaheim pepper": 100,  # 1 medium Anaheim
    "habanero pepper": 10,  # 1 pepper
    "onion": 150,           # 1 medium onion
    "red onion": 150,       # 1 medium onion
    "yellow onion": 150,    # 1 medium onion
    "white onion": 150,     # 1 medium onion
    "green onion": 15,      # 1 stalk/scallion
    "scallion": 15,         # 1 stalk
    "shallot": 40,          # 1 medium shallot
    "leek": 100,            # 1 medium leek
    "tomato": 150,          # 1 medium tomato
    "cherry tomato": 15,    # 1 tomato
    "grape tomato": 10,     # 1 tomato
    "potato": 200,          # 1 medium potato
    "sweet potato": 200,    # 1 medium
    "zucchini": 200,        # 1 medium zucchini
    "cucumber": 300,        # 1 medium cucumber
    "broccoli": 150,        # 1 crown/head
    "cauliflower": 500,     # 1 head
    "brussels sprout": 20,  # 1 sprout
    "celery": 40,           # 1 stalk
    "garlic": 5,            # 1 clove
    "ginger": 50,           # 1 knob (thumb-sized)
    "mushroom": 18,         # 1 medium button mushroom
    "portobello mushroom": 100, # 1 cap
    "shiitake mushroom": 15, # 1 mushroom
    "spinach": 30,          # 1 cup fresh (loosely packed)
    "kale": 35,             # 1 cup chopped
    "lettuce": 500,         # 1 head romaine
    "tomatillo": 60,        # 1 medium tomatillo
    "fennel": 250,          # 1 medium fennel bulb
    "parsnip": 150,         # 1 medium parsnip
    "turnip": 150,          # 1 medium turnip
    "bok choy": 500,        # 1 head
    "baby bok choy": 200,   # 1 head
    "butternut squash": 700,  # 1 medium squash
    "acorn squash": 500,    # 1 medium squash
    "artichoke": 150,       # 1 medium globe artichoke
    "okra": 15,             # 1 pod
    "green bean": 10,       # 1 bean
    "asparagus": 20,        # 1 spear
    "corn": 200,            # 1 cob
    "eggplant": 450,        # 1 medium
    "radish": 15,           # 1 radish
    "beet": 100,            # 1 medium beet

    # Fruits
    "apple": 180,           # 1 medium apple
    "banana": 120,          # 1 medium banana
    "orange": 140,          # 1 medium orange
    "lemon": 58,            # 1 medium lemon
    "lime": 44,             # 1 medium lime
    "avocado": 150,         # 1 medium avocado
    "strawberry": 15,       # 1 medium berry
    "blueberry": 1,         # 1 berry
    "raspberry": 1,         # 1 berry
    "mango": 200,           # 1 medium mango
    "pineapple": 900,       # 1 whole pineapple
    "pear": 180,            # 1 medium pear
    "peach": 150,           # 1 medium peach
    "plum": 70,             # 1 medium plum
    "grape": 5,             # 1 grape
    "cherry": 8,            # 1 cherry
    "nectarine": 140,       # 1 medium nectarine
    "apricot": 45,          # 1 medium apricot
    "fig": 40,              # 1 fresh fig
    "kiwi": 75,             # 1 medium kiwi
    "pomegranate": 250,     # 1 medium pomegranate

    # Fresh Herbs (by bunch/package)
    "basil": 25,            # 1 bunch (typical grocery package)
    "cilantro": 25,         # 1 bunch
    "parsley": 30,          # 1 bunch
    "mint": 20,             # 1 bunch
    "thyme": 10,            # 1 bunch (smaller)
    "rosemary": 15,         # 1 bunch
    "dill": 20,             # 1 bunch

    # Additional proteins
    "lamb chop": 125,       # 1 rib chop
    "duck breast": 200,     # 1 breast half
    "scallop": 35,          # 1 large scallop

    # Eggs & Dairy (if not packaged)
    "egg": 50,              # 1 large egg

    # Plant-based proteins
    "tofu": 350,            # 1 block (standard package)
    "tempeh": 240,          # 1 package

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
