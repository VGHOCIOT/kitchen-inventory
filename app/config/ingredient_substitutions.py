"""
Ingredient substitution seed data.

Defines common cooking substitutions with conversion ratios and quality scores.
Seeded via the /api/v1/recipes/seed-substitutions endpoint.

Format:
    original: canonical ingredient name being replaced
    substitute: canonical ingredient name to use instead
    ratio: quantity multiplier (1.0 = same amount, 0.75 = use 25% less)
    quality_score: 1-10 (5+ shown to users, 8+ excellent drop-in)
    bidirectional: if True, seeder creates both directions (reverse ratio auto-calculated)

Names must match canonical ingredient names from ingredient_aliases.py or fresh_weights.py.
"""

INGREDIENT_SUBSTITUTION_SEEDS: list[dict] = [
    # ── Dairy & Fats ─────────────────────────────────────────────────────────
    {
        "original": "butter",
        "substitute": "margarine",
        "ratio": 1.0,
        "quality_score": 8,
        "notes": "Good for most cooking; less ideal for flaky pastry",
        "bidirectional": True,
    },
    {
        "original": "butter",
        "substitute": "coconut oil",
        "ratio": 0.8,
        "quality_score": 7,
        "notes": "Use less coconut oil; adds slight coconut flavor",
        "bidirectional": True,
    },
    {
        "original": "butter",
        "substitute": "olive oil",
        "ratio": 0.75,
        "quality_score": 6,
        "notes": "Works for sautéing; not suitable for baking",
        "bidirectional": False,
    },
    {
        "original": "sour cream",
        "substitute": "greek yogurt",
        "ratio": 1.0,
        "quality_score": 9,
        "notes": "Excellent swap; similar tang and consistency",
        "bidirectional": True,
    },
    {
        "original": "heavy cream",
        "substitute": "coconut cream",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Works for curries and soups; adds coconut flavor",
        "bidirectional": True,
    },
    {
        "original": "cream cheese",
        "substitute": "ricotta",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Lighter texture; works in dips and fillings",
        "bidirectional": True,
    },

    # ── Cooking Oils ─────────────────────────────────────────────────────────
    {
        "original": "olive oil",
        "substitute": "vegetable oil",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Neutral flavor; good for high-heat cooking",
        "bidirectional": True,
    },
    {
        "original": "vegetable oil",
        "substitute": "canola oil",
        "ratio": 1.0,
        "quality_score": 9,
        "notes": "Near-identical for cooking purposes",
        "bidirectional": True,
    },
    {
        "original": "sesame oil",
        "substitute": "olive oil",
        "ratio": 1.0,
        "quality_score": 5,
        "notes": "Loses sesame flavor; works as a base oil substitute only",
        "bidirectional": False,
    },

    # ── Sweeteners ───────────────────────────────────────────────────────────
    {
        "original": "sugar",
        "substitute": "honey",
        "ratio": 0.75,
        "quality_score": 7,
        "notes": "Use less honey; reduce other liquids slightly in baking",
        "bidirectional": False,
    },
    {
        "original": "sugar",
        "substitute": "maple syrup",
        "ratio": 0.75,
        "quality_score": 7,
        "notes": "Use less syrup; reduce other liquids slightly in baking",
        "bidirectional": False,
    },
    {
        "original": "honey",
        "substitute": "maple syrup",
        "ratio": 1.0,
        "quality_score": 8,
        "notes": "Similar sweetness and consistency",
        "bidirectional": True,
    },
    {
        "original": "brown sugar",
        "substitute": "sugar",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Loses molasses depth; add a splash of molasses if available",
        "bidirectional": False,
    },

    # ── Herbs ────────────────────────────────────────────────────────────────
    {
        "original": "parsley",
        "substitute": "cilantro",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Different flavor profile; works as garnish",
        "bidirectional": True,
    },
    {
        "original": "thyme",
        "substitute": "oregano",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Similar earthy profile; common in Mediterranean cooking",
        "bidirectional": True,
    },
    {
        "original": "basil",
        "substitute": "oregano",
        "ratio": 0.75,
        "quality_score": 5,
        "notes": "Oregano is stronger; use less",
        "bidirectional": False,
    },
    {
        "original": "dill",
        "substitute": "fennel",
        "ratio": 0.5,
        "quality_score": 5,
        "notes": "Similar anise notes; fennel is stronger",
        "bidirectional": False,
    },
    {
        "original": "rosemary",
        "substitute": "thyme",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Both are woody herbs; works in roasts and stews",
        "bidirectional": True,
    },
    {
        "original": "mint",
        "substitute": "basil",
        "ratio": 1.0,
        "quality_score": 5,
        "notes": "Works in some salads and Thai dishes; different flavor",
        "bidirectional": False,
    },

    # ── Alliums ──────────────────────────────────────────────────────────────
    {
        "original": "onion",
        "substitute": "shallot",
        "ratio": 0.5,
        "quality_score": 8,
        "notes": "Shallots are more concentrated; use less by weight",
        "bidirectional": False,
    },
    {
        "original": "shallot",
        "substitute": "onion",
        "ratio": 2.0,
        "quality_score": 7,
        "notes": "Use more onion; milder flavor",
        "bidirectional": False,
    },
    {
        "original": "green onion",
        "substitute": "chives",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Similar mild onion flavor; best as garnish",
        "bidirectional": True,
    },
    {
        "original": "red onion",
        "substitute": "onion",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Loses color; slightly different flavor when raw",
        "bidirectional": True,
    },
    {
        "original": "leek",
        "substitute": "onion",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Onion is sharper; works in cooked dishes",
        "bidirectional": False,
    },

    # ── Acids / Citrus ───────────────────────────────────────────────────────
    {
        "original": "lemon",
        "substitute": "lime",
        "ratio": 1.0,
        "quality_score": 9,
        "notes": "Nearly interchangeable in most recipes",
        "bidirectional": True,
    },
    {
        "original": "white vinegar",
        "substitute": "apple cider vinegar",
        "ratio": 1.0,
        "quality_score": 8,
        "notes": "Slightly fruity; works in dressings and marinades",
        "bidirectional": True,
    },
    {
        "original": "rice vinegar",
        "substitute": "apple cider vinegar",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "ACV is slightly stronger; works in Asian-style dressings",
        "bidirectional": False,
    },

    # ── Proteins ─────────────────────────────────────────────────────────────
    {
        "original": "chicken breast",
        "substitute": "chicken thigh",
        "ratio": 1.0,
        "quality_score": 8,
        "notes": "Thigh is fattier and more forgiving; great swap",
        "bidirectional": True,
    },
    {
        "original": "ground beef",
        "substitute": "ground turkey",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Leaner; works in tacos, pasta sauce, meatballs",
        "bidirectional": True,
    },
    {
        "original": "ground beef",
        "substitute": "ground chicken",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Much leaner; may need added fat for moisture",
        "bidirectional": False,
    },
    {
        "original": "shrimp",
        "substitute": "scallop",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Different texture; works in stir-fries and pastas",
        "bidirectional": True,
    },
    {
        "original": "salmon",
        "substitute": "tuna",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Different fat content; works for steaks and grilling",
        "bidirectional": True,
    },
    {
        "original": "tofu",
        "substitute": "tempeh",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Tempeh is firmer with nuttier flavor; crumble or slice",
        "bidirectional": True,
    },

    # ── Vegetables ───────────────────────────────────────────────────────────
    {
        "original": "potato",
        "substitute": "sweet potato",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Sweeter flavor; works for roasting, mashing, soups",
        "bidirectional": True,
    },
    {
        "original": "spinach",
        "substitute": "kale",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Kale is tougher; cook longer or massage if raw",
        "bidirectional": True,
    },
    {
        "original": "broccoli",
        "substitute": "cauliflower",
        "ratio": 1.0,
        "quality_score": 8,
        "notes": "Very similar cooking properties; milder flavor",
        "bidirectional": True,
    },
    {
        "original": "zucchini",
        "substitute": "eggplant",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Different texture; works in stir-fries and grilling",
        "bidirectional": True,
    },
    {
        "original": "bell pepper",
        "substitute": "red bell pepper",
        "ratio": 1.0,
        "quality_score": 9,
        "notes": "Red is sweeter; otherwise identical",
        "bidirectional": True,
    },
    {
        "original": "bell pepper",
        "substitute": "green bell pepper",
        "ratio": 1.0,
        "quality_score": 9,
        "notes": "Green is more bitter; otherwise identical",
        "bidirectional": True,
    },
    {
        "original": "butternut squash",
        "substitute": "sweet potato",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "Similar sweetness and texture when roasted or in soups",
        "bidirectional": True,
    },
    {
        "original": "mushroom",
        "substitute": "portobello mushroom",
        "ratio": 1.0,
        "quality_score": 8,
        "notes": "Larger but same family; slice to match",
        "bidirectional": True,
    },
    {
        "original": "mushroom",
        "substitute": "shiitake mushroom",
        "ratio": 1.0,
        "quality_score": 7,
        "notes": "More umami; great in Asian dishes",
        "bidirectional": True,
    },

    # ── Tomatoes ──────────────────────────────────────────────────────────────
    {
        "original": "tomato",
        "substitute": "cherry tomato",
        "ratio": 1.0,
        "quality_score": 8,
        "notes": "Sweeter; use same weight, halved or quartered",
        "bidirectional": True,
    },

    # ── Eggs ─────────────────────────────────────────────────────────────────
    {
        "original": "egg",
        "substitute": "banana",
        "ratio": 1.0,
        "quality_score": 5,
        "notes": "1 egg ≈ 1 mashed banana; for baking only, adds sweetness",
        "bidirectional": False,
    },

    # ── Starches & Grains ────────────────────────────────────────────────────
    {
        "original": "all-purpose flour",
        "substitute": "whole wheat flour",
        "ratio": 1.0,
        "quality_score": 6,
        "notes": "Denser result; may need slightly more liquid",
        "bidirectional": True,
    },
]
