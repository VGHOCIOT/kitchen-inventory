"""Tests for service-layer functions (ingredient_mapper, recipe_matcher, cook_service)."""

import uuid
from models.item import Locations


# ── ingredient_mapper ─────────────────────────────────────────────────────────

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


class TestFindSubstitution:
    async def test_quality_filter(self, db_session, make_ingredient, make_substitution, make_product, make_alias, make_stock):
        from api.services.recipe_matcher import find_substitution_for_ingredient, aggregate_inventory_by_ingredient

        butter = await make_ingredient(name="butter")
        lard = await make_ingredient(name="lard")

        p_lard = await make_product(name="Lard Tub", package_quantity=500, package_unit="g")
        await make_alias("Lard Tub", lard.id)
        await make_stock(p_lard.id, Locations.FRIDGE, 500.0, "g")

        # Quality score 4 — below threshold
        await make_substitution(butter.id, lard.id, ratio=1.0, quality_score=4)

        inventory = await aggregate_inventory_by_ingredient(db_session)
        result = await find_substitution_for_ingredient(db_session, butter.id, inventory)
        assert result is None

    async def test_prefers_sufficient_quantity(
        self, db_session, make_ingredient, make_substitution, make_product, make_alias, make_stock
    ):
        from api.services.recipe_matcher import find_substitution_for_ingredient, aggregate_inventory_by_ingredient

        butter = await make_ingredient(name="butter")
        margarine = await make_ingredient(name="margarine")
        coconut_oil = await make_ingredient(name="coconut oil")

        p_marg = await make_product(name="Margarine", package_quantity=50, package_unit="g")
        p_coco = await make_product(name="Coconut Oil", package_quantity=500, package_unit="g")
        await make_alias("Margarine", margarine.id)
        await make_alias("Coconut Oil", coconut_oil.id)
        await make_stock(p_marg.id, Locations.FRIDGE, 50.0, "g")  # Not enough
        await make_stock(p_coco.id, Locations.CUPBOARD, 500.0, "g")  # Enough

        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)
        await make_substitution(butter.id, coconut_oil.id, ratio=0.8, quality_score=7)

        inventory = await aggregate_inventory_by_ingredient(db_session)
        result = await find_substitution_for_ingredient(
            db_session, butter.id, inventory,
            required_quantity=200.0, required_unit="g",
        )
        # Should prefer coconut oil (sufficient qty) over margarine (insufficient)
        assert result is not None
        assert result.substitute_ingredient_name == "coconut oil"


# ── cook_service ──────────────────────────────────────────────────────────────

class TestCookService:
    async def test_basic_cook(self, db_session, populated_inventory):
        from api.services.cook_service import cook_recipe

        recipe = populated_inventory["recipe"]
        result = await cook_recipe(db_session, recipe.id)

        assert result is not None
        assert result["recipe_title"] == "Simple Cookies"
        assert len(result["deducted"]) == 3
        assert len(result["insufficient"]) == 0
        assert len(result["unmapped"]) == 0

    async def test_cook_with_explicit_substitution(self, db_session, make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution):
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

        result = await cook_recipe(
            db_session, recipe.id,
            substitutions={str(butter.id): str(margarine.id)},
        )
        assert len(result["substituted"]) == 1
        assert result["substituted"][0]["substitute"] == "margarine"
        assert result["substituted"][0]["amount"] == 50.0

    async def test_cook_auto_substitution(self, db_session, make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution):
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

        # No explicit substitution — should auto-find margarine
        result = await cook_recipe(db_session, recipe.id)
        assert len(result["substituted"]) == 1
        assert result["substituted"][0]["substitute"] == "margarine"

    async def test_cook_insufficient(self, db_session, make_product, make_ingredient, make_alias, make_stock, make_recipe):
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
        assert len(result["insufficient"]) == 1
        assert result["insufficient"][0]["needed"] == 500.0
        assert result["insufficient"][0]["available"] == 100.0

    async def test_cook_unmapped(self, db_session, make_ingredient, make_recipe):
        from api.services.cook_service import cook_recipe

        saffron = await make_ingredient(name="saffron")
        recipe = await make_recipe(
            title="Fancy Rice",
            ingredients=[{"text": "saffron", "ingredient_id": saffron.id, "quantity": 1.0, "unit": "g"}],
        )

        result = await cook_recipe(db_session, recipe.id)
        assert "saffron" in result["unmapped"]

    async def test_cook_not_found(self, db_session):
        from api.services.cook_service import cook_recipe

        result = await cook_recipe(db_session, uuid.uuid4())
        assert result is None
