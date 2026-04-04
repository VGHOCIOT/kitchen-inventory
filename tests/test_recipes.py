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


class TestRecipeDuplicatePrevention:
    async def test_duplicate_recipe_ingredient_text_raises_integrity_error(self, db_session, make_recipe, make_ingredient):
        """
        The (recipe_id, ingredient_text) unique constraint prevents the same raw
        ingredient line from being linked to a recipe twice. A direct double-insert
        must raise IntegrityError — this is the DB-level last line of defence.
        """
        import pytest
        from sqlalchemy.exc import IntegrityError
        from models.recipe_ingredient import RecipeIngredient

        ing = await make_ingredient(name="butter")
        recipe = await make_recipe(title="Constraint Test")

        db_session.add(RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_text="2 tbsp butter",
            canonical_ingredient_id=ing.id,
            quantity=28.0,
            unit="g",
        ))
        await db_session.commit()

        db_session.add(RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_text="2 tbsp butter",
            canonical_ingredient_id=ing.id,
            quantity=28.0,
            unit="g",
        ))
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_get_recipe_ingredient_by_text_returns_existing(self, db_session, make_recipe, make_ingredient):
        """
        get_recipe_ingredient_by_text returns the row when it exists, None when not.
        Used by the recipe endpoint to skip duplicate ingredient lines.
        """
        from crud.recipe_ingredient import create_recipe_ingredient, get_recipe_ingredient_by_text

        ing = await make_ingredient(name="butter")
        recipe = await make_recipe(title="Text Lookup Test")

        await create_recipe_ingredient(
            db_session,
            recipe_id=recipe.id,
            ingredient_text="2 tbsp butter",
            canonical_ingredient_id=ing.id,
            quantity=28.0,
            unit="g",
        )

        found = await get_recipe_ingredient_by_text(db_session, recipe.id, "2 tbsp butter")
        assert found is not None
        assert found.ingredient_text == "2 tbsp butter"

        not_found = await get_recipe_ingredient_by_text(db_session, recipe.id, "1 cup flour")
        assert not_found is None


class TestMatchInventory:
    async def test_no_recipes(self, client):
        resp = await client.get("/api/v1/recipes/match-inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["unlocked"] == []
        assert data["almost"] == []
        assert data["locked"] == []
        assert data["total_recipes_checked"] == 0

    async def test_unlocked(self, client, populated_inventory):
        """All ingredients in stock — recipe should be unlocked at 100%."""
        resp = await client.get("/api/v1/recipes/match-inventory")
        data = resp.json()
        assert len(data["unlocked"]) == 1
        assert data["unlocked"][0]["recipe_title"] == "Simple Cookies"
        assert data["unlocked"][0]["availability_percent"] == 100.0

    async def test_locked_missing_ingredient(self, client, make_product, make_ingredient, make_alias, make_stock, make_recipe):
        """2/3 ingredients in stock (66.7%) — below 70% threshold, goes to locked."""
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
        assert len(data["locked"]) == 1
        assert data["locked"][0]["missing_ingredients"] == ["egg"]

    async def test_substitution_counts_as_unlocked(
        self, client, make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution
    ):
        """Substitution covers a missing ingredient — counts as 100%, goes to unlocked."""
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
        # Substitution covers butter → 2/2 = 100% → unlocked
        assert len(data["unlocked"]) == 1
        subs = data["unlocked"][0]["suggested_substitutions"]
        assert len(subs) == 1
        assert subs[0]["substitute_ingredient_name"] == "margarine"
        # butter not in missing_ingredients since substitution covers it
        assert "butter" not in data["unlocked"][0]["missing_ingredients"]

    async def test_almost(self, client, make_product, make_ingredient, make_alias, make_stock, make_recipe):
        """3/4 ingredients in stock (75%) — above 70%, goes to almost."""
        from models.item import Locations

        butter = await make_ingredient(name="butter")
        flour = await make_ingredient(name="flour")
        sugar = await make_ingredient(name="sugar")
        egg = await make_ingredient(name="egg")

        p_butter = await make_product(name="Butter Block", package_quantity=227, package_unit="g")
        p_flour = await make_product(name="Bread Flour", package_quantity=1000, package_unit="g")
        p_sugar = await make_product(name="White Sugar", package_quantity=500, package_unit="g")
        await make_alias("Butter Block", butter.id)
        await make_alias("Bread Flour", flour.id)
        await make_alias("White Sugar", sugar.id)
        await make_stock(p_butter.id, Locations.FRIDGE, 227.0, "g")
        await make_stock(p_flour.id, Locations.CUPBOARD, 1000.0, "g")
        await make_stock(p_sugar.id, Locations.CUPBOARD, 500.0, "g")

        await make_recipe(
            title="Egg Cookies",
            ingredients=[
                {"text": "butter", "ingredient_id": butter.id, "quantity": 113.0, "unit": "g"},
                {"text": "flour", "ingredient_id": flour.id, "quantity": 240.0, "unit": "g"},
                {"text": "sugar", "ingredient_id": sugar.id, "quantity": 100.0, "unit": "g"},
                {"text": "egg", "ingredient_id": egg.id, "quantity": 1.0, "unit": "unit"},
            ],
        )

        resp = await client.get("/api/v1/recipes/match-inventory")
        data = resp.json()
        assert len(data["almost"]) == 1
        assert data["almost"][0]["missing_ingredients"] == ["egg"]


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
