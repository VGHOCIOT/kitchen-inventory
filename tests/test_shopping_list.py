"""Tests for shopping list endpoint."""

import uuid


class TestShoppingList:
    async def test_fully_stocked(self, client, populated_inventory):
        """All ingredients available — nothing to buy."""
        recipe = populated_inventory["recipe"]
        resp = await client.post(
            "/api/v1/shopping-list/from-recipes",
            json={"recipe_ids": [str(recipe.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 0
        assert "butter" in data["fully_stocked"]
        assert "flour" in data["fully_stocked"]
        assert "sugar" in data["fully_stocked"]

    async def test_no_stock(self, client, make_ingredient, make_recipe):
        """Nothing in inventory — all ingredients to buy."""
        butter = await make_ingredient(name="butter")
        flour = await make_ingredient(name="flour")

        recipe = await make_recipe(
            title="Shortbread",
            ingredients=[
                {"text": "butter", "ingredient_id": butter.id, "quantity": 200.0, "unit": "g"},
                {"text": "flour", "ingredient_id": flour.id, "quantity": 300.0, "unit": "g"},
            ],
        )

        resp = await client.post(
            "/api/v1/shopping-list/from-recipes",
            json={"recipe_ids": [str(recipe.id)]},
        )
        data = resp.json()
        assert len(data["items"]) == 2
        names = {item["ingredient_name"] for item in data["items"]}
        assert names == {"butter", "flour"}

    async def test_partial_stock(self, client, make_product, make_ingredient, make_alias, make_stock, make_recipe):
        from models.item import Locations

        flour = await make_ingredient(name="flour")
        p_flour = await make_product(name="Flour Bag", package_quantity=500, package_unit="g")
        await make_alias("Flour Bag", flour.id)
        await make_stock(p_flour.id, Locations.CUPBOARD, 100.0, "g")

        recipe = await make_recipe(
            title="Bread",
            ingredients=[
                {"text": "flour", "ingredient_id": flour.id, "quantity": 500.0, "unit": "g"},
            ],
        )

        resp = await client.post(
            "/api/v1/shopping-list/from-recipes",
            json={"recipe_ids": [str(recipe.id)]},
        )
        data = resp.json()
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["required_quantity"] == 500.0
        assert item["available_quantity"] == 100.0
        assert item["to_buy_quantity"] == 400.0

    async def test_consolidates_across_recipes(self, client, make_ingredient, make_recipe):
        flour = await make_ingredient(name="flour")

        r1 = await make_recipe(
            title="Bread",
            ingredients=[{"text": "flour", "ingredient_id": flour.id, "quantity": 300.0, "unit": "g"}],
        )
        r2 = await make_recipe(
            title="Cake",
            ingredients=[{"text": "flour", "ingredient_id": flour.id, "quantity": 200.0, "unit": "g"}],
        )

        resp = await client.post(
            "/api/v1/shopping-list/from-recipes",
            json={"recipe_ids": [str(r1.id), str(r2.id)]},
        )
        data = resp.json()
        flour_item = next(i for i in data["items"] if i["ingredient_name"] == "flour")
        assert flour_item["required_quantity"] == 500.0
        assert set(flour_item["from_recipes"]) == {"Bread", "Cake"}

    async def test_substitution_hint(
        self, client, make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution
    ):
        from models.item import Locations

        butter = await make_ingredient(name="butter")
        margarine = await make_ingredient(name="margarine")

        p_marg = await make_product(name="Margarine", package_quantity=454, package_unit="g")
        await make_alias("Margarine", margarine.id)
        await make_stock(p_marg.id, Locations.FRIDGE, 454.0, "g")

        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)

        recipe = await make_recipe(
            title="Toast",
            ingredients=[{"text": "butter", "ingredient_id": butter.id, "quantity": 50.0, "unit": "g"}],
        )

        resp = await client.post(
            "/api/v1/shopping-list/from-recipes",
            json={"recipe_ids": [str(recipe.id)]},
        )
        data = resp.json()
        butter_item = next(i for i in data["items"] if i["ingredient_name"] == "butter")
        assert butter_item["substitution_available"] is not None
        assert butter_item["substitution_available"]["substitute_ingredient_name"] == "margarine"

    async def test_unknown_recipe_ignored(self, client, make_recipe):
        recipe = await make_recipe(title="Real Recipe")
        resp = await client.post(
            "/api/v1/shopping-list/from-recipes",
            json={"recipe_ids": [str(recipe.id), str(uuid.uuid4())]},
        )
        assert resp.status_code == 200
        assert resp.json()["recipe_count"] == 2
