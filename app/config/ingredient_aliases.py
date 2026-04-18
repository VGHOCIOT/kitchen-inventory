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
    "ground chicken": ["minced chicken", "chicken mince"],
    "chicken wing": ["chicken wings", "chicken wingette", "chicken wingettes", "party wings"],
    "whole chicken": ["roasting chicken", "broiler chicken", "fryer chicken"],
    "turkey breast": ["turkey breast roast", "boneless turkey breast", "sliced turkey breast"],
    "ground turkey": ["minced turkey", "turkey mince", "lean ground turkey"],
    "pork chop": ["pork chops", "boneless pork chop", "boneless pork chops", "pork loin chop", "pork loin chops"],
    "pork tenderloin": ["pork tenderloin roast", "pork loin"],
    "pork belly": ["pork belly slices", "uncured pork belly"],
    "italian sausage": ["italian sausages", "mild italian sausage", "hot italian sausage", "sweet italian sausage"],
    "breakfast sausage": ["breakfast sausages", "pork breakfast sausage", "maple breakfast sausage"],
    "chorizo": ["chorizo sausage", "spanish chorizo", "mexican chorizo"],
    "kielbasa": ["kielbasa sausage", "polish sausage", "smoked kielbasa"],
    "hot dog": ["hot dogs", "frankfurter", "frankfurters", "wiener", "wieners"],
    "steak": ["beef steak", "grilling steak"],
    "ribeye steak": ["ribeye", "rib eye steak", "rib eye", "rib-eye steak", "rib-eye"],
    "sirloin steak": ["sirloin", "top sirloin steak", "top sirloin"],
    "flank steak": ["flank", "london broil"],
    "ground lamb": ["minced lamb", "lamb mince"],

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
    "poblano pepper": [
        "poblano", "poblanos", "poblano peppers",
        "pasilla pepper", "pasilla peppers",
    ],
    "habanero pepper": ["habanero", "habaneros", "habanero peppers"],
    "anaheim pepper": ["anaheim", "anaheims", "anaheim peppers"],

    # ── Root vegetables ────────────────────────────────────────────────────────
    "carrot": ["carrots", "baby carrot", "baby carrots"],
    "potato": ["potatoes", "white potato", "white potatoes", "russet potato", "russet potatoes"],
    "sweet potato": ["sweet potatoes", "yam", "yams"],
    "beet": ["beets", "beetroot", "beetroots"],

    # ── Squash ─────────────────────────────────────────────────────────────────
    "butternut squash": ["butternut", "butternut squashes"],
    "acorn squash": ["acorn squashes"],

    # ── Aromatics ──────────────────────────────────────────────────────────────
    "fennel": ["fennel bulb", "fennel bulbs"],

    # ── Brassicas ──────────────────────────────────────────────────────────────
    "broccoli": ["broccoli floret", "broccoli florets", "broccoli crown", "broccoli crowns"],
    "brussels sprout": ["brussels sprouts", "brussel sprout", "brussel sprouts"],
    "bok choy": ["bok choys", "pak choi", "pak choy"],
    "baby bok choy": ["baby bok choys", "baby pak choi"],

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
    "scallop": ["scallops", "sea scallop", "sea scallops", "bay scallop", "bay scallops"],
    "lamb chop": ["lamb chops", "lamb rib chop", "lamb rib chops"],
    "duck breast": ["duck breasts"],

    # ── Fruits ─────────────────────────────────────────────────────────────────
    "avocado": ["avocados", "hass avocado", "hass avocados"],
    "lemon": ["lemons"],
    "lime": ["limes"],
    "kiwi": ["kiwis", "kiwifruit"],
    "fig": ["figs", "fresh fig", "fresh figs"],
    "pomegranate": ["pomegranates"],

    # ── Ginger / aromatics ─────────────────────────────────────────────────────
    "ginger": ["fresh ginger", "ginger root", "ginger knob"],

    # ── Eggs ───────────────────────────────────────────────────────────────────
    "egg": ["eggs", "large egg", "large eggs"],

    # ── Plant-based ────────────────────────────────────────────────────────────
    "tofu": ["firm tofu", "extra firm tofu", "silken tofu", "soft tofu"],

    # ── Dairy (CA store labels → US recipe names) ─────────────────────────────
    "heavy cream": [
        "whipping cream", "heavy whipping cream", "cooking cream", "single cream",
    ],
    "light cream": [
        "table cream", "coffee cream",
    ],
    "half and half": [
        "half and half cream", "half & half",
    ],
    "whole milk": [
        "homogenized milk", "homo milk",
    ],
    "milk": [
        "2% milk", "2 percent milk", "reduced fat milk",
        "skim milk", "skimmed milk", "non-fat milk",
        "low-fat milk", "1% milk",
    ],
    "chicken broth": [
        "chicken stock", "chicken stock broth",
        "low sodium chicken broth", "low sodium chicken stock",
    ],
    "beef broth": [
        "beef stock", "beef stock broth",
        "low sodium beef broth", "low sodium beef stock",
    ],
    "vegetable broth": [
        "vegetable stock", "veggie broth", "veggie stock",
        "low sodium vegetable broth", "low sodium vegetable stock",
    ],
    "cream cheese": [
        "brick cream cheese", "spreadable cream cheese",
    ],
    "buttermilk": ["cultured buttermilk"],
    "butter": [
        "unsalted butter", "salted butter",
    ],

    # ── Baking (CA store labels → US recipe names) ────────────────────────────
    "powdered sugar": [
        "icing sugar", "confectioners sugar", "confectioners' sugar",
        "confectioner's sugar",
    ],
    "granulated sugar": [
        "white sugar", "cane sugar", "sugar",
    ],
    "brown sugar": [
        "golden brown sugar", "dark brown sugar",
        "light brown sugar", "demerara sugar",
    ],
    "all-purpose flour": [
        "all purpose flour", "all purpose flour white",
        "white flour", "plain flour", "ap flour",
    ],
    "whole wheat flour": [
        "whole wheat", "whole grain flour", "wholemeal flour", "wholemeal",
        "whole-wheat flour", "whole grain",
    ],
    "bread flour": [
        "strong flour", "strong white flour", "high gluten flour",
    ],
    "bread crumbs": [
        "breadcrumbs", "bread crumb", "panko", "panko bread crumbs",
        "panko breadcrumbs", "dried bread crumbs",
    ],
    "baking soda": [
        "bicarbonate of soda", "bicarb", "sodium bicarbonate",
    ],
    "cornstarch": [
        "corn starch", "cornflour", "corn flour",
    ],
    "vanilla extract": [
        "vanilla", "pure vanilla extract", "vanilla essence",
    ],
    "cocoa powder": [
        "cocoa", "unsweetened cocoa", "unsweetened cocoa powder",
        "dutch process cocoa", "dutch cocoa",
    ],

    # ── Oils ──────────────────────────────────────────────────────────────────
    "olive oil": [
        "extra virgin olive oil", "evoo", "virgin olive oil",
    ],
    "vegetable oil": [
        "canola oil", "rapeseed oil", "cooking oil",
    ],

    # ── Salt & Seasoning ──────────────────────────────────────────────────────
    "salt": [
        "table salt", "iodized salt", "iodized table salt",
        "kosher salt", "sea salt", "fine salt", "coarse salt",
    ],
    "black pepper": [
        "pepper", "ground black pepper", "cracked black pepper",
        "freshly ground black pepper", "ground pepper",
    ],

    # ── Produce (CA/UK names → US recipe names) ──────────────────────────────
    "zucchini": ["courgette", "courgettes", "zucchinis"],
    "eggplant": ["aubergine", "aubergines", "eggplants"],
    "arugula": ["rocket", "roquette", "garden rocket"],
    "green bean": [
        "green beans", "string bean", "string beans",
        "french bean", "french beans", "haricot vert", "haricots verts",
    ],
    "corn": ["sweet corn", "corn on the cob", "corn kernels"],

    # ── Meat (CA store labels → US recipe names) ──────────────────────────────
    "ground beef": [
        "minced beef", "beef mince", "hamburger meat",
        "lean ground beef", "extra lean ground beef", "medium ground beef",
    ],
    "ground pork": ["minced pork", "pork mince"],
    "ground turkey": ["minced turkey", "turkey mince"],
    "bacon": ["streaky bacon", "side bacon", "strip bacon", "pork bacon"],
    "turkey bacon": [
        "turkey bacon strips",
        "butterball turkey bacon",
        "lean turkey bacon",
        "smoked turkey bacon",
    ],
    "chicken bacon": [
        "chicken bacon strips",
        "halal chicken bacon",
        "smoked chicken bacon",
    ],
    "canadian bacon": ["back bacon", "peameal bacon"],

    # ── Legumes ───────────────────────────────────────────────────────────────
    "chickpea": ["chickpeas", "garbanzo bean", "garbanzo beans", "garbanzo"],
    "fava bean": ["fava beans", "broad bean", "broad beans"],
    "lentil": ["lentils", "red lentil", "red lentils", "green lentil", "green lentils"],
    "black beans": ["black bean", "canned black beans", "dried black beans"],
    "kidney beans": ["kidney bean", "canned kidney beans", "red kidney beans", "dark red kidney beans"],
    "navy beans": [
        "navy bean", "white bean", "white beans",
        "great northern bean", "great northern beans",
        "cannellini bean", "cannellini beans",
    ],
    "pinto beans": ["pinto bean", "canned pinto beans", "dried pinto beans"],

    # ── Pantry / Condiments ───────────────────────────────────────────────────
    "soy sauce": ["soya sauce"],
    "tamari": ["gluten-free soy sauce", "san-j tamari", "wheat-free soy sauce"],
    "coconut aminos": ["coconut aminos sauce", "coconut secret aminos"],
    "molasses": ["treacle", "blackstrap molasses"],
    "maple syrup": ["pure maple syrup"],
    "worcestershire sauce": ["worcestershire", "lea & perrins worcestershire sauce", "lea and perrins"],
    "hot sauce": ["tabasco", "frank's redhot", "crystal hot sauce", "louisiana hot sauce"],
    "sriracha": ["sriracha sauce", "huy fong sriracha", "rooster sauce"],
    "mayonnaise": ["mayo", "light mayonnaise", "olive oil mayonnaise", "avocado oil mayo"],
    "ketchup": ["tomato ketchup", "heinz ketchup", "catsup"],
    "mustard": ["yellow mustard", "prepared mustard", "french's mustard"],
    "dijon mustard": ["dijon", "smooth dijon mustard", "old style dijon", "whole grain dijon"],

    # ── Pantry (concentrated / processed forms) ───────────────────────────────
    "tomato paste": ["double concentrate tomato paste", "tomato concentré", "tomato concentrate"],
    "canned tomatoes": [
        "diced tomatoes", "canned diced tomatoes",
        "crushed tomatoes", "canned crushed tomatoes",
        "whole canned tomatoes", "whole peeled tomatoes",
        "san marzano tomatoes",
    ],
    "tomato sauce": ["passata", "strained tomatoes", "pureed tomatoes", "sieved tomatoes"],
    "evaporated milk": ["carnation evaporated milk", "evaporated skim milk", "evaporated 2% milk"],
    "lemon juice": ["bottled lemon juice", "pure lemon juice"],
    "lime juice": ["bottled lime juice", "pure lime juice"],

    # ── Dairy (additional) ────────────────────────────────────────────────────
    "sour cream": ["light sour cream", "fat-free sour cream", "14% sour cream", "dairy sour cream"],
    "greek yogurt": [
        "plain greek yogurt", "0% greek yogurt", "2% greek yogurt",
        "non-fat greek yogurt", "oikos", "chobani",
    ],
    "yogurt": ["plain yogurt", "natural yogurt", "regular yogurt", "balkan style yogurt"],
    "ghee": ["clarified butter", "pure ghee", "desi ghee", "organic ghee"],
    "ricotta": ["ricotta cheese", "part skim ricotta", "fresh ricotta"],
    "margarine": ["non-hydrogenated margarine", "light margarine", "soft margarine"],

    # ── Dairy (plant-based) ───────────────────────────────────────────────────
    "oat milk": ["oat milk beverage", "oat-based beverage", "oatly", "unsweetened oat milk"],
    "almond milk": ["almond milk beverage", "unsweetened almond milk", "original almond milk"],
    "coconut milk": ["canned coconut milk", "light coconut milk", "coconut milk beverage"],
    "coconut cream": ["canned coconut cream", "thai coconut cream"],
    "coconut oil": ["organic coconut oil", "refined coconut oil", "virgin coconut oil", "extra virgin coconut oil"],

    # ── Cheeses ───────────────────────────────────────────────────────────────
    "cheddar": [
        "cheddar cheese", "old cheddar", "mild cheddar", "medium cheddar",
        "sharp cheddar", "aged cheddar", "white cheddar", "shredded cheddar",
    ],
    "mozzarella": [
        "mozzarella cheese", "fresh mozzarella", "part skim mozzarella",
        "shredded mozzarella", "buffalo mozzarella",
    ],
    "parmesan": [
        "parmigiano reggiano", "parmigiano", "grated parmesan",
        "shredded parmesan", "parmesan cheese",
    ],
    "feta": ["feta cheese", "greek feta", "crumbled feta", "feta in brine"],
    "swiss cheese": ["swiss", "emmental", "emmenthal", "gruyère", "gruyere"],
    "provolone": ["provolone cheese", "provolone slices"],

    # ── Spices & Dried Herbs ──────────────────────────────────────────────────
    "cumin": ["ground cumin", "cumin powder", "cumin seed", "cumin seeds"],
    "paprika": ["sweet paprika", "smoked paprika", "hungarian paprika"],
    "turmeric": ["ground turmeric", "turmeric powder"],
    "chili powder": ["chile powder", "chili seasoning blend"],
    "cayenne": ["cayenne pepper", "ground cayenne", "cayenne pepper powder"],
    "cinnamon": ["ground cinnamon", "cinnamon powder"],
    "coriander": ["ground coriander", "coriander powder", "coriander seed"],
    "garlic powder": ["garlic granules"],
    "onion powder": ["onion granules"],
    "ground ginger": ["ginger powder", "powdered ginger"],
    "dried oregano": ["oregano", "mediterranean oregano"],
    "dried thyme": ["thyme leaves"],
    "dried basil": ["basil leaves"],
    "dried rosemary": ["rosemary leaves"],
    "dried dill": ["dill weed", "dill tips"],
    "bay leaf": ["bay leaves", "dried bay leaf", "dried bay leaves"],
    "chili flakes": ["red pepper flakes", "crushed red pepper", "crushed chili flakes"],
    "allspice": ["ground allspice"],
    "nutmeg": ["ground nutmeg"],
    "cardamom": ["ground cardamom", "cardamom pods"],
    "cloves": ["ground cloves", "whole cloves"],

    # ── Vinegars ─────────────────────────────────────────────────────────────
    "apple cider vinegar": ["acv", "unpasteurized apple cider vinegar", "bragg apple cider vinegar"],
    "rice vinegar": ["rice wine vinegar", "seasoned rice vinegar", "unseasoned rice vinegar"],
    "balsamic vinegar": ["balsamic", "balsamic vinegar of modena", "aged balsamic"],
    "white vinegar": ["distilled white vinegar", "white distilled vinegar", "spirit vinegar"],
    "red wine vinegar": ["red wine vinegar"],

    # ── Grains & Starches ─────────────────────────────────────────────────────
    "white rice": ["long grain white rice", "enriched white rice", "medium grain white rice"],
    "brown rice": ["long grain brown rice", "whole grain brown rice"],
    "jasmine rice": ["thai jasmine rice", "fragrant rice"],
    "basmati rice": ["aged basmati", "indian basmati rice", "long grain basmati"],
    "quinoa": ["white quinoa", "mixed quinoa", "tri-color quinoa", "red quinoa"],
    "oats": [
        "rolled oats", "quick oats", "old fashioned oats",
        "instant oats", "steel cut oats",
    ],
    "spaghetti": ["thin spaghetti", "spaghettini", "spaghetti noodles"],
    "penne": ["penne rigate", "penne lisce", "penne pasta"],
    "fettuccine": ["fettucine", "fettuccine pasta", "fettuccine noodles"],
    "linguine": ["linguini", "linguine pasta"],
    "farfalle": ["bowtie pasta", "bow tie pasta", "bow-tie pasta"],
    "rigatoni": ["rigatoni pasta"],
    "rotini": ["rotini pasta", "fusilli", "spiral pasta"],
    "elbow macaroni": ["elbow pasta", "macaroni", "mac"],
    "lasagna noodles": ["lasagne", "lasagna pasta", "lasagna sheets"],

    # ── Nut Butters & Spreads ─────────────────────────────────────────────────
    "peanut butter": [
        "natural peanut butter", "smooth peanut butter",
        "crunchy peanut butter", "creamy peanut butter",
    ],
    "almond butter": ["natural almond butter", "smooth almond butter", "crunchy almond butter"],
    "tahini": ["sesame paste", "sesame tahini", "roasted tahini", "raw tahini"],
}
