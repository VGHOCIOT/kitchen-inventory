"""Tests for recipe endpoints."""

import uuid


class TestListRecipes:
    async def test_empty(self, client):
        resp = await client.get("/api/v1/recipes/")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_after_create(self, client, make_recipe):
        await make_recipe(title="Pasta Carbonara")
        await make_recipe(title="Chicken Stir Fry")

        resp = await client.get("/api/v1/recipes/")
        data = resp.json()
        assert len(data) == 2
        titles = {r["title"] for r in data}
        assert titles == {"Pasta Carbonara", "Chicken Stir Fry"}


class TestGetRecipe:
    async def test_get_by_id(self, client, make_recipe, make_ingredient):
        ing = await make_ingredient(name="pasta")
        recipe = await make_recipe(
            title="Simple Pasta",
            ingredients=[{"text": "pasta", "ingredient_id": ing.id, "quantity": 200.0, "unit": "g"}],
        )

        resp = await client.get(f"/api/v1/recipes/{recipe.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["recipe"]["title"] == "Simple Pasta"
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["quantity"] == 200.0

    async def test_not_found(self, client):
        resp = await client.get(f"/api/v1/recipes/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestDeleteRecipe:
    async def test_delete(self, client, make_recipe):
        recipe = await make_recipe(title="To Delete")

        resp = await client.delete(f"/api/v1/recipes/{recipe.id}")
        assert resp.status_code == 204

        resp = await client.get(f"/api/v1/recipes/{recipe.id}")
        assert resp.status_code == 404

    async def test_delete_not_found(self, client):
        resp = await client.delete(f"/api/v1/recipes/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestMatchInventory:
    async def test_no_recipes(self, client):
        resp = await client.get("/api/v1/recipes/match-inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["can_make_now"] == []
        assert data["total_recipes_checked"] == 0

    async def test_can_make_now(self, client, populated_inventory):
        """All ingredients in stock — recipe should appear in can_make_now."""
        resp = await client.get("/api/v1/recipes/match-inventory")
        data = resp.json()
        assert len(data["can_make_now"]) == 1
        assert data["can_make_now"][0]["recipe_title"] == "Simple Cookies"
        assert data["can_make_now"][0]["availability_percent"] == 100.0

    async def test_missing_one(self, client, make_product, make_ingredient, make_alias, make_stock, make_recipe):
        from models.item import Locations

        butter = await make_ingredient(name="butter")
        flour = await make_ingredient(name="flour")
        egg = await make_ingredient(name="egg")

        p_butter = await make_product(name="Butter Block", package_quantity=227, package_unit="g")
        p_flour = await make_product(name="Bread Flour", package_quantity=1000, package_unit="g")
        await make_alias("Butter Block", butter.id)
        await make_alias("Bread Flour", flour.id)
        await make_stock(p_butter.id, Locations.FRIDGE, 227.0, "g")
        await make_stock(p_flour.id, Locations.CUPBOARD, 1000.0, "g")

        await make_recipe(
            title="Cookies",
            ingredients=[
                {"text": "butter", "ingredient_id": butter.id, "quantity": 113.0, "unit": "g"},
                {"text": "flour", "ingredient_id": flour.id, "quantity": 240.0, "unit": "g"},
                {"text": "egg", "ingredient_id": egg.id, "quantity": 1.0, "unit": "unit"},
            ],
        )

        resp = await client.get("/api/v1/recipes/match-inventory")
        data = resp.json()
        assert len(data["missing_one"]) == 1

    async def test_with_substitutions(
        self, client, make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution
    ):
        from models.item import Locations

        butter = await make_ingredient(name="butter")
        flour = await make_ingredient(name="flour")
        margarine = await make_ingredient(name="margarine")

        p_flour = await make_product(name="Plain Flour", package_quantity=1000, package_unit="g")
        p_marg = await make_product(name="Margarine Tub", package_quantity=454, package_unit="g")
        await make_alias("Plain Flour", flour.id)
        await make_alias("Margarine Tub", margarine.id)
        await make_stock(p_flour.id, Locations.CUPBOARD, 1000.0, "g")
        await make_stock(p_marg.id, Locations.FRIDGE, 454.0, "g")

        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)

        await make_recipe(
            title="Butter Cake",
            ingredients=[
                {"text": "butter", "ingredient_id": butter.id, "quantity": 200.0, "unit": "g"},
                {"text": "flour", "ingredient_id": flour.id, "quantity": 300.0, "unit": "g"},
            ],
        )

        resp = await client.get("/api/v1/recipes/match-inventory")
        data = resp.json()
        # 1 missing ingredient → goes to missing_one, with substitution attached
        assert len(data["missing_one"]) == 1
        subs = data["missing_one"][0]["suggested_substitutions"]
        assert len(subs) == 1
        assert subs[0]["substitute_ingredient_name"] == "margarine"


class TestSeedEndpoints:
    async def test_seed_aliases(self, client):
        resp = await client.post("/api/v1/recipes/seed-aliases")
        assert resp.status_code == 200
        data = resp.json()
        assert data["aliases_created"] > 0

        # Idempotent — second call creates nothing
        resp2 = await client.post("/api/v1/recipes/seed-aliases")
        assert resp2.json()["aliases_created"] == 0

    async def test_seed_substitutions(self, client):
        resp = await client.post("/api/v1/recipes/seed-substitutions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] > 0

        # Idempotent
        resp2 = await client.post("/api/v1/recipes/seed-substitutions")
        assert resp2.json()["created"] == 0
