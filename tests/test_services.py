"""Tests for service-layer functions (ingredient_mapper, recipe_matcher, cook_service)."""

import uuid
from models.item import Locations


# ── ingredient_mapper ─────────────────────────────────────────────────────────

class TestOpenfoodHelpers:
    def test_strip_package_size_grams(self):
        from api.services.openfood import strip_package_size
        assert strip_package_size("Beef Broth 400 g") == "Beef Broth"

    def test_strip_package_size_ml(self):
        from api.services.openfood import strip_package_size
        assert strip_package_size("Tomato Soup 2x300ml") == "Tomato Soup"

    def test_strip_package_size_no_suffix(self):
        from api.services.openfood import strip_package_size
        assert strip_package_size("Peanut Butter") == "Peanut Butter"

    def test_strip_package_size_empty(self):
        from api.services.openfood import strip_package_size
        assert strip_package_size("") == ""

    def test_name_from_categories_skips_taxonomy_tags(self):
        from api.services.openfood import _name_from_categories
        categories = ["Farming products", "Eggs", "Chicken eggs", "en:large-eggs"]
        assert _name_from_categories(categories) == "Chicken eggs"

    def test_name_from_categories_all_taxonomy(self):
        """All en: tags → returns empty string."""
        from api.services.openfood import _name_from_categories
        assert _name_from_categories(["en:eggs", "en:large-eggs"]) == ""

    def test_name_from_categories_empty(self):
        from api.services.openfood import _name_from_categories
        assert _name_from_categories([]) == ""

    def test_name_from_categories_mixed_case_tag(self):
        """Tag detection is case-insensitive (EN: should also be excluded)."""
        from api.services.openfood import _name_from_categories
        result = _name_from_categories(["Dairy", "EN:whole-milk"])
        assert result == "Dairy"


class TestGetAliasByText:
    async def test_case_insensitive_lookup(self, db_session, make_ingredient, make_alias):
        from crud.ingredient_alias import get_alias_by_text

        ing = await make_ingredient(name="butter")
        await make_alias("Store Butter", ing.id)

        assert await get_alias_by_text(db_session, "store butter") is not None
        assert await get_alias_by_text(db_session, "STORE BUTTER") is not None
        assert await get_alias_by_text(db_session, "Store Butter") is not None

    async def test_returns_none_when_missing(self, db_session):
        from crud.ingredient_alias import get_alias_by_text

        assert await get_alias_by_text(db_session, "Nonexistent Product") is None

    async def test_unique_constraint_on_alias(self, db_session, make_ingredient):
        """
        The alias column has a unique constraint — a second insert of the same alias
        text must raise an IntegrityError from the DB. This is the last line of
        defence; callers (seeding, auto_map) check for existence before inserting.
        """
        import pytest
        from sqlalchemy.exc import IntegrityError
        from models.ingredient_alias import IngredientAlias

        ing = await make_ingredient(name="sugar")
        db_session.add(IngredientAlias(alias="White Sugar", ingredient_id=ing.id))
        await db_session.commit()

        db_session.add(IngredientAlias(alias="White Sugar", ingredient_id=ing.id))
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestAutoMapProduct:
    async def test_maps_via_fuzzy_match(self, db_session, make_ingredient):
        from api.services.ingredient_mapper import auto_map_product_to_ingredient
        from crud.ingredient_alias import get_alias_by_text

        await make_ingredient(name="olive oil")
        await auto_map_product_to_ingredient(db_session, "Extra Virgin Olive Oil")

        alias = await get_alias_by_text(db_session, "Extra Virgin Olive Oil")
        assert alias is not None

    async def test_already_aliased_is_noop(self, db_session, make_ingredient, make_alias):
        from api.services.ingredient_mapper import auto_map_product_to_ingredient

        ing = await make_ingredient(name="butter")
        await make_alias("Store Butter", ing.id)

        # Should not raise or create duplicates
        await auto_map_product_to_ingredient(db_session, "Store Butter")

    async def test_maps_via_normalized_alias_before_fuzzy(self, db_session, make_ingredient, make_alias):
        """
        Step 3 of the pipeline: if the normalized product name resolves through an
        existing alias, the product name is mapped to that ingredient — fuzzy match
        (step 4) must NOT fire.
        """
        from api.services.ingredient_mapper import auto_map_product_to_ingredient
        from crud.ingredient_alias import get_alias_by_text

        # "whole grain flour" is the normalized form of the product name
        # "whole wheat flour" is the canonical ingredient
        # We pre-seed an alias so normalized lookup (step 3) can find it
        wheat_flour = await make_ingredient(name="whole wheat flour")
        await make_alias("whole grain flour", wheat_flour.id)

        await auto_map_product_to_ingredient(db_session, "Organic Whole Grain Flour")

        alias = await get_alias_by_text(db_session, "Organic Whole Grain Flour")
        assert alias is not None
        assert alias.ingredient_id == wheat_flour.id

    async def test_no_match_no_alias(self, db_session):
        from api.services.ingredient_mapper import auto_map_product_to_ingredient
        from crud.ingredient_alias import get_alias_by_text

        await auto_map_product_to_ingredient(db_session, "Xylitol Sweetener")
        alias = await get_alias_by_text(db_session, "Xylitol Sweetener")
        assert alias is None


# ── recipe_matcher ────────────────────────────────────────────────────────────

class TestAggregateInventory:
    async def test_empty_inventory(self, db_session):
        from api.services.recipe_matcher import aggregate_inventory_by_ingredient

        inventory = await aggregate_inventory_by_ingredient(db_session)
        assert inventory == {}

    async def test_basic_aggregation(self, db_session, make_product, make_ingredient, make_alias, make_stock):
        from api.services.recipe_matcher import aggregate_inventory_by_ingredient

        butter = await make_ingredient(name="butter")
        product = await make_product(name="Store Butter", package_quantity=227, package_unit="g")
        await make_alias("Store Butter", butter.id)
        await make_stock(product.id, Locations.FRIDGE, 227.0, "g")

        inventory = await aggregate_inventory_by_ingredient(db_session)
        assert butter.id in inventory
        assert inventory[butter.id].total_quantity == 227.0

    async def test_multiple_products_same_ingredient(
        self, db_session, make_product, make_ingredient, make_alias, make_stock
    ):
        from api.services.recipe_matcher import aggregate_inventory_by_ingredient

        butter = await make_ingredient(name="butter")
        p1 = await make_product(name="Butter A", package_quantity=227, package_unit="g")
        p2 = await make_product(name="Butter B", package_quantity=454, package_unit="g")
        await make_alias("Butter A", butter.id)
        await make_alias("Butter B", butter.id)
        await make_stock(p1.id, Locations.FRIDGE, 227.0, "g")
        await make_stock(p2.id, Locations.FRIDGE, 454.0, "g")

        inventory = await aggregate_inventory_by_ingredient(db_session)
        assert inventory[butter.id].total_quantity == 681.0


class TestFindSubstitutions:
    async def test_no_result_when_substitute_not_in_inventory(
        self, db_session, make_ingredient, make_substitution
    ):
        """Substitute exists in the substitution table but has no stock — returns empty list."""
        from api.services.recipe_matcher import find_substitutions_for_ingredient, aggregate_inventory_by_ingredient

        butter = await make_ingredient(name="butter")
        lard = await make_ingredient(name="lard")
        await make_substitution(butter.id, lard.id, ratio=1.0, quality_score=8)

        inventory = await aggregate_inventory_by_ingredient(db_session)
        result = await find_substitutions_for_ingredient(db_session, butter.id, inventory)
        assert result == []

    async def test_filters_insufficient_stock(
        self, db_session, make_ingredient, make_substitution, make_product, make_alias, make_stock
    ):
        """Substitute with insufficient stock for the required quantity is excluded."""
        from api.services.recipe_matcher import find_substitutions_for_ingredient, aggregate_inventory_by_ingredient

        butter = await make_ingredient(name="butter")
        lard = await make_ingredient(name="lard")

        p_lard = await make_product(name="Lard Tub", package_quantity=500, package_unit="g")
        await make_alias("Lard Tub", lard.id)
        await make_stock(p_lard.id, Locations.FRIDGE, 50.0, "g")  # only 50g available

        await make_substitution(butter.id, lard.id, ratio=1.0, quality_score=8)

        inventory = await aggregate_inventory_by_ingredient(db_session)
        result = await find_substitutions_for_ingredient(
            db_session, butter.id, inventory,
            required_quantity=200.0, required_unit="g",
        )
        assert result == []

    async def test_prefers_sufficient_quantity(
        self, db_session, make_ingredient, make_substitution, make_product, make_alias, make_stock
    ):
        """When one sub has insufficient stock, the sufficient one is returned first."""
        from api.services.recipe_matcher import find_substitutions_for_ingredient, aggregate_inventory_by_ingredient

        butter = await make_ingredient(name="butter")
        margarine = await make_ingredient(name="margarine")
        coconut_oil = await make_ingredient(name="coconut oil")

        p_marg = await make_product(name="Margarine", package_quantity=50, package_unit="g")
        p_coco = await make_product(name="Coconut Oil", package_quantity=500, package_unit="g")
        await make_alias("Margarine", margarine.id)
        await make_alias("Coconut Oil", coconut_oil.id)
        await make_stock(p_marg.id, Locations.FRIDGE, 50.0, "g")   # Not enough for 200g
        await make_stock(p_coco.id, Locations.CUPBOARD, 500.0, "g")  # Enough

        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)
        await make_substitution(butter.id, coconut_oil.id, ratio=0.8, quality_score=7)

        inventory = await aggregate_inventory_by_ingredient(db_session)
        result = await find_substitutions_for_ingredient(
            db_session, butter.id, inventory,
            required_quantity=200.0, required_unit="g",
        )
        # Only coconut oil has sufficient qty (500 >= 200*0.8=160); margarine (50 < 200) excluded
        assert len(result) == 1
        assert result[0].substitute_ingredient_name == "coconut oil"

    async def test_sorted_by_quality_score(
        self, db_session, make_ingredient, make_substitution, make_product, make_alias, make_stock
    ):
        """Results are sorted highest quality_score first."""
        from api.services.recipe_matcher import find_substitutions_for_ingredient, aggregate_inventory_by_ingredient

        butter = await make_ingredient(name="butter")
        lard = await make_ingredient(name="lard")
        coconut_oil = await make_ingredient(name="coconut oil")

        p_lard = await make_product(name="Lard Tub", package_quantity=500, package_unit="g")
        p_coco = await make_product(name="Coconut Oil", package_quantity=500, package_unit="g")
        await make_alias("Lard Tub", lard.id)
        await make_alias("Coconut Oil", coconut_oil.id)
        await make_stock(p_lard.id, Locations.FRIDGE, 500.0, "g")
        await make_stock(p_coco.id, Locations.CUPBOARD, 500.0, "g")

        await make_substitution(butter.id, lard.id, ratio=1.0, quality_score=6)
        await make_substitution(butter.id, coconut_oil.id, ratio=0.8, quality_score=9)

        inventory = await aggregate_inventory_by_ingredient(db_session)
        result = await find_substitutions_for_ingredient(
            db_session, butter.id, inventory,
            required_quantity=100.0, required_unit="g",
        )
        assert len(result) == 2
        assert result[0].substitute_ingredient_name == "coconut oil"  # quality 9
        assert result[1].substitute_ingredient_name == "lard"          # quality 6


# ── cook_service ──────────────────────────────────────────────────────────────

class TestCookService:
    async def test_basic_cook(self, db_session, populated_inventory):
        from api.services.cook_service import cook_recipe

        recipe = populated_inventory["recipe"]
        result = await cook_recipe(db_session, recipe.id)

        assert result is not None
        assert result["recipe_title"] == "Simple Cookies"
        assert len(result["deducted"]) == 3
        assert result["failed"] == []

    async def test_cook_with_explicit_substitution(
        self, db_session, make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution
    ):
        from api.services.cook_service import cook_recipe

        butter = await make_ingredient(name="butter")
        margarine = await make_ingredient(name="margarine")

        p_marg = await make_product(name="Margarine Stick", package_quantity=454, package_unit="g")
        await make_alias("Margarine Stick", margarine.id)
        await make_stock(p_marg.id, Locations.FRIDGE, 454.0, "g")

        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)

        recipe = await make_recipe(
            title="Butter Toast",
            ingredients=[{"text": "butter", "ingredient_id": butter.id, "quantity": 50.0, "unit": "g"}],
        )

        # Pass UUIDs (not strings) — the endpoint converts strings; the service expects UUID objects
        result = await cook_recipe(
            db_session, recipe.id,
            substitutions={butter.id: margarine.id},
        )
        assert result["failed"] == []
        deducted_names = [d["ingredient"] for d in result["deducted"]]
        assert "margarine" in deducted_names

    async def test_cook_auto_substitution(
        self, db_session, make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution
    ):
        from api.services.cook_service import cook_recipe

        butter = await make_ingredient(name="butter")
        margarine = await make_ingredient(name="margarine")

        p_marg = await make_product(name="Marg Block", package_quantity=454, package_unit="g")
        await make_alias("Marg Block", margarine.id)
        await make_stock(p_marg.id, Locations.FRIDGE, 454.0, "g")

        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)

        recipe = await make_recipe(
            title="Garlic Bread",
            ingredients=[{"text": "butter", "ingredient_id": butter.id, "quantity": 100.0, "unit": "g"}],
        )

        # No butter stock — should auto-find margarine and deduct it
        result = await cook_recipe(db_session, recipe.id)
        assert result["failed"] == []
        deducted_names = [d["ingredient"] for d in result["deducted"]]
        assert "margarine" in deducted_names

    async def test_cook_preflight_fails_when_insufficient_no_sub(
        self, db_session, make_product, make_ingredient, make_alias, make_stock, make_recipe
    ):
        """Pre-flight aborts and returns empty deducted when an ingredient is insufficient with no substitute."""
        from api.services.cook_service import cook_recipe

        flour = await make_ingredient(name="flour")
        p_flour = await make_product(name="Flour Sack", package_quantity=500, package_unit="g")
        await make_alias("Flour Sack", flour.id)
        await make_stock(p_flour.id, Locations.CUPBOARD, 100.0, "g")

        recipe = await make_recipe(
            title="Big Cake",
            ingredients=[{"text": "flour", "ingredient_id": flour.id, "quantity": 500.0, "unit": "g"}],
        )

        result = await cook_recipe(db_session, recipe.id)
        assert result["deducted"] == []
        assert "flour" in result["failed"]

    async def test_cook_missing_ingredient_goes_to_failed(
        self, db_session, make_ingredient, make_recipe
    ):
        """Ingredients with no stock and no substitute end up in failed."""
        from api.services.cook_service import cook_recipe

        saffron = await make_ingredient(name="saffron")
        recipe = await make_recipe(
            title="Fancy Rice",
            ingredients=[{"text": "saffron", "ingredient_id": saffron.id, "quantity": 1.0, "unit": "g"}],
        )

        result = await cook_recipe(db_session, recipe.id)
        assert "saffron" in result["failed"]

    async def test_cook_not_found(self, db_session):
        from api.services.cook_service import cook_recipe

        result = await cook_recipe(db_session, uuid.uuid4())
        assert result is None


# ── get_cook_plan ─────────────────────────────────────────────────────────────

class TestGetCookPlan:
    async def test_returns_none_for_unknown_recipe(self, db_session):
        from api.services.cook_service import get_cook_plan

        result = await get_cook_plan(db_session, uuid.uuid4())
        assert result is None

    async def test_available_status_when_sufficient_stock(
        self, db_session, make_product, make_ingredient, make_alias, make_stock, make_recipe
    ):
        from api.services.cook_service import get_cook_plan

        flour = await make_ingredient(name="flour")
        p_flour = await make_product(name="Flour Bag", package_quantity=1000, package_unit="g")
        await make_alias("Flour Bag", flour.id)
        await make_stock(p_flour.id, Locations.CUPBOARD, 1000.0, "g")

        recipe = await make_recipe(
            title="Pancakes",
            ingredients=[{"text": "flour", "ingredient_id": flour.id, "quantity": 200.0, "unit": "g"}],
        )

        plan = await get_cook_plan(db_session, recipe.id)
        assert plan is not None
        assert plan.recipe_title == "Pancakes"
        assert len(plan.ingredients) == 1
        assert plan.ingredients[0].status == "available"
        assert plan.ingredients[0].ingredient_name == "flour"

    async def test_insufficient_status_with_substitute_listed(
        self, db_session, make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution
    ):
        from api.services.cook_service import get_cook_plan

        butter = await make_ingredient(name="butter")
        margarine = await make_ingredient(name="margarine")

        p_butter = await make_product(name="Store Butter", package_quantity=227, package_unit="g")
        p_marg = await make_product(name="Margarine Tub", package_quantity=454, package_unit="g")
        await make_alias("Store Butter", butter.id)
        await make_alias("Margarine Tub", margarine.id)
        await make_stock(p_butter.id, Locations.FRIDGE, 50.0, "g")   # not enough
        await make_stock(p_marg.id, Locations.FRIDGE, 454.0, "g")

        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)

        recipe = await make_recipe(
            title="Shortbread",
            ingredients=[{"text": "butter", "ingredient_id": butter.id, "quantity": 200.0, "unit": "g"}],
        )

        plan = await get_cook_plan(db_session, recipe.id)
        assert plan is not None
        ing = plan.ingredients[0]
        assert ing.status == "insufficient"
        assert len(ing.substitutes) == 1
        assert ing.substitutes[0].substitute_ingredient_name == "margarine"

    async def test_missing_status_when_no_stock(
        self, db_session, make_ingredient, make_recipe
    ):
        from api.services.cook_service import get_cook_plan

        saffron = await make_ingredient(name="saffron")
        recipe = await make_recipe(
            title="Paella",
            ingredients=[{"text": "saffron", "ingredient_id": saffron.id, "quantity": 1.0, "unit": "g"}],
        )

        plan = await get_cook_plan(db_session, recipe.id)
        assert plan is not None
        assert plan.ingredients[0].status == "missing"
        assert plan.ingredients[0].substitutes == []
