"""
Explicit ingredient alias seed data.

This covers cases that can't be auto-resolved by plural/singular logic:
- Regional name variations (scallions, spring onions → green onion)
- Common modifier stripping (boneless skinless chicken breast → chicken breast)
- Synonyms (cilantro → coriander)

Format: { "canonical_name": ["alias1", "alias2", ...] }

Canonical names must match entries in fresh_weights.py or be known ingredients.
These are seeded via the /api/v1/recipes/seed-aliases endpoint.
"""

INGREDIENT_ALIAS_SEEDS: dict[str, list[str]] = {
    # ── Alliums ────────────────────────────────────────────────────────────────
    "green onion": [
        "scallion", "scallions",
        "spring onion", "spring onions",
        "green onions",
    ],
    "onion": [
        "onions",
        "yellow onion", "yellow onions",
        "white onion", "white onions",
        "sweet onion", "sweet onions",
        "cooking onion", "cooking onions",
    ],
    "red onion": [
        "red onions",
        "purple onion", "purple onions",
    ],
    "shallot": ["shallots", "eschallot", "eschallots"],
    "garlic": ["garlic clove", "garlic cloves"],

    # ── Poultry ────────────────────────────────────────────────────────────────
    "chicken breast": [
        "chicken breasts",
        "boneless chicken breast", "boneless chicken breasts",
        "skinless chicken breast", "skinless chicken breasts",
        "boneless skinless chicken breast", "boneless skinless chicken breasts",
    ],
    "chicken thigh": [
        "chicken thighs",
        "boneless chicken thigh", "boneless chicken thighs",
        "skinless chicken thigh", "skinless chicken thighs",
        "boneless skinless chicken thigh", "boneless skinless chicken thighs",
    ],
    "chicken leg": ["chicken legs", "drumstick", "drumsticks"],

    # ── Peppers ────────────────────────────────────────────────────────────────
    "bell pepper": [
        "bell peppers",
        "capsicum", "capsicums",
        "sweet pepper", "sweet peppers",
    ],
    "red bell pepper": [
        "red bell peppers",
        "red pepper", "red peppers",
        "red capsicum",
    ],
    "green bell pepper": [
        "green bell peppers",
        "green pepper", "green peppers",
        "green capsicum",
    ],
    "jalapeño": [
        "jalapeno", "jalapenos", "jalapeños",
        "jalapeño pepper", "jalapeño peppers",
        "jalapeno pepper", "jalapeno peppers",
    ],

    # ── Root vegetables ────────────────────────────────────────────────────────
    "carrot": ["carrots", "baby carrot", "baby carrots"],
    "potato": ["potatoes", "white potato", "white potatoes", "russet potato", "russet potatoes"],
    "sweet potato": ["sweet potatoes", "yam", "yams"],
    "beet": ["beets", "beetroot", "beetroots"],

    # ── Brassicas ──────────────────────────────────────────────────────────────
    "broccoli": ["broccoli floret", "broccoli florets", "broccoli crown", "broccoli crowns"],
    "brussels sprout": ["brussels sprouts", "brussel sprout", "brussel sprouts"],

    # ── Fungi ──────────────────────────────────────────────────────────────────
    "mushroom": [
        "mushrooms",
        "button mushroom", "button mushrooms",
        "cremini mushroom", "cremini mushrooms",
        "crimini mushroom", "crimini mushrooms",
        "white mushroom", "white mushrooms",
    ],
    "shiitake mushroom": ["shiitake mushrooms", "shiitake", "shiitakes"],
    "portobello mushroom": [
        "portobello mushrooms",
        "portabella mushroom", "portabella mushrooms",
        "portobella mushroom", "portobella mushrooms",
    ],

    # ── Leafy greens ───────────────────────────────────────────────────────────
    "spinach": ["baby spinach", "fresh spinach"],
    "kale": ["curly kale", "lacinato kale", "dinosaur kale"],
    "lettuce": [
        "romaine lettuce", "romaine",
        "iceberg lettuce", "iceberg",
        "boston lettuce", "butter lettuce",
    ],

    # ── Tomatoes ───────────────────────────────────────────────────────────────
    "tomato": ["tomatoes", "roma tomato", "roma tomatoes", "plum tomato", "plum tomatoes"],
    "cherry tomato": ["cherry tomatoes"],
    "grape tomato": ["grape tomatoes"],

    # ── Herbs ──────────────────────────────────────────────────────────────────
    "cilantro": ["coriander", "coriander leaves", "fresh cilantro", "fresh coriander"],
    "parsley": ["flat leaf parsley", "italian parsley", "curly parsley", "fresh parsley"],
    "basil": ["fresh basil", "sweet basil"],
    "mint": ["fresh mint", "spearmint"],
    "thyme": ["fresh thyme"],
    "rosemary": ["fresh rosemary"],
    "dill": ["fresh dill", "dill weed"],

    # ── Seafood ────────────────────────────────────────────────────────────────
    "shrimp": ["prawns", "prawn", "large shrimp", "jumbo shrimp"],
    "salmon": ["salmon fillet", "salmon fillets", "salmon steak", "atlantic salmon"],
    "tuna": ["tuna steak", "tuna steaks", "ahi tuna"],

    # ── Fruits ─────────────────────────────────────────────────────────────────
    "avocado": ["avocados", "hass avocado", "hass avocados"],
    "lemon": ["lemons"],
    "lime": ["limes"],

    # ── Ginger / aromatics ─────────────────────────────────────────────────────
    "ginger": ["fresh ginger", "ginger root", "ginger knob"],

    # ── Eggs ───────────────────────────────────────────────────────────────────
    "egg": ["eggs", "large egg", "large eggs"],

    # ── Plant-based ────────────────────────────────────────────────────────────
    "tofu": ["firm tofu", "extra firm tofu", "silken tofu", "soft tofu"],
}
