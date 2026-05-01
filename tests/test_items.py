"""Tests for item/inventory endpoints."""

import uuid


class TestListItems:
    async def test_empty(self, client):
        resp = await client.get("/api/v1/items/")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_after_add(self, client, make_product, make_stock):
        product = await make_product(name="Carrots", package_quantity=500, package_unit="g")
        await make_stock(product.id, quantity=500.0, unit="g")

        resp = await client.get("/api/v1/items/")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["item"]["qty"] == 500.0
        assert data[0]["product"]["name"] == "Carrots"

    async def test_unit_field_present_and_correct_for_weight(self, client, make_product, make_stock):
        """
        ItemWithProductOut must expose item.unit so the frontend formatQty
        function can distinguish grams from ml from unit.
        """
        product = await make_product(name="Flour", package_quantity=1000, package_unit="g")
        await make_stock(product.id, quantity=1000.0, unit="g")

        resp = await client.get("/api/v1/items/")
        item = resp.json()[0]["item"]
        assert item["unit"] == "g"
        assert item["qty"] == 1000.0

    async def test_unit_field_ml_for_liquid(self, client, make_product, make_stock):
        product = await make_product(name="Olive Oil", package_quantity=750, package_unit="ml")
        await make_stock(product.id, quantity=750.0, unit="ml")

        item = (await client.get("/api/v1/items/")).json()[0]["item"]
        assert item["unit"] == "ml"

    async def test_unit_field_unit_for_count(self, client, make_product, make_stock):
        """
        Count-based items that couldn't be resolved to grams surface as 'unit'
        in the API response — the frontend must not crash on this.
        """
        product = await make_product(name="Mystery Item", package_quantity=5, package_unit="unit")
        await make_stock(product.id, quantity=5.0, unit="unit")

        item = (await client.get("/api/v1/items/")).json()[0]["item"]
        assert item["unit"] == "unit"
        assert item["qty"] == 5.0

    async def test_items_across_locations_have_correct_units(self, client, make_product, make_stock):
        """
        The same product stocked at two locations must independently carry
        the correct unit in ItemWithProductOut — both consumed by the
        InventoryPage location filter.
        """
        from models.item import Locations

        product = await make_product(name="Butter", package_quantity=227, package_unit="g")
        await make_stock(product.id, Locations.FRIDGE, 227.0, "g")
        await make_stock(product.id, Locations.FREEZER, 454.0, "g")

        all_items = (await client.get("/api/v1/items/")).json()
        assert len(all_items) == 2
        for entry in all_items:
            assert entry["item"]["unit"] == "g"

    async def test_by_location(self, client, make_product, make_stock):
        from models.item import Locations

        product = await make_product(name="Milk", package_quantity=1000, package_unit="ml")
        await make_stock(product.id, Locations.FRIDGE, 1000.0, "ml")

        resp = await client.get("/api/v1/items/location/fridge")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp = await client.get("/api/v1/items/location/cupboard")
        assert resp.status_code == 200
        assert len(resp.json()) == 0


class TestAddFresh:
    async def test_add_fresh_item(self, client):
        resp = await client.post(
            "/api/v1/items/add-fresh",
            json={"name": "Bananas", "weight_grams": 300.0, "location": "fridge"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["item"]["qty"] == 300.0
        assert data["item"]["unit"] == "g"
        assert data["item"]["location"] == "fridge"
        assert data["product_reference"]["name"] == "Bananas"

    async def test_add_fresh_defaults_to_fridge(self, client):
        """location defaults to fridge when omitted from body."""
        resp = await client.post(
            "/api/v1/items/add-fresh",
            json={"name": "Grapes", "weight_grams": 100.0},
        )
        assert resp.status_code == 200
        assert resp.json()["item"]["location"] == "fridge"

    async def test_add_fresh_explicit_location(self, client):
        """location in body routes stock to correct location."""
        resp = await client.post(
            "/api/v1/items/add-fresh",
            json={"name": "Frozen Peas", "weight_grams": 500.0, "location": "freezer"},
        )
        assert resp.status_code == 200
        assert resp.json()["item"]["location"] == "freezer"

    async def test_add_fresh_location_as_query_param_ignored(self, client):
        """Passing location as a query param (old API) is now ignored — body wins."""
        resp = await client.post(
            "/api/v1/items/add-fresh?location=freezer",
            json={"name": "Berries", "weight_grams": 200.0, "location": "fridge"},
        )
        assert resp.status_code == 200
        assert resp.json()["item"]["location"] == "fridge"

    async def test_add_fresh_twice_sums_qty(self, client):
        await client.post(
            "/api/v1/items/add-fresh",
            json={"name": "Apples", "weight_grams": 200.0, "location": "fridge"},
        )
        resp = await client.post(
            "/api/v1/items/add-fresh",
            json={"name": "Apples", "weight_grams": 150.0, "location": "fridge"},
        )
        assert resp.status_code == 200
        assert resp.json()["item"]["qty"] == 350.0


class TestLotsForItem:
    async def test_list_lots(self, client, make_product, make_stock):
        from models.item import Locations

        product = await make_product(name="Rice", package_quantity=1000, package_unit="g")
        await make_stock(product.id, Locations.CUPBOARD, 500.0, "g")
        await make_stock(product.id, Locations.CUPBOARD, 300.0, "g")

        resp = await client.get(f"/api/v1/items/lots/{product.id}/cupboard")
        assert resp.status_code == 200
        lots = resp.json()
        assert len(lots) == 2
        # FIFO order: first lot first
        assert lots[0]["remaining_quantity"] == 500.0
        assert lots[1]["remaining_quantity"] == 300.0


class TestAdjustQuantity:
    async def test_positive_delta(self, client, make_product, make_stock):
        product = await make_product(name="Flour", package_quantity=1000, package_unit="g")
        await make_stock(product.id, quantity=500.0, unit="g")

        resp = await client.patch(
            "/api/v1/items/adjust",
            json={
                "product_reference_id": str(product.id),
                "location": "fridge",
                "delta": 200.0,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["qty"] == 700.0

    async def test_negative_delta(self, client, make_product, make_stock):
        product = await make_product(name="Sugar", package_quantity=1000, package_unit="g")
        await make_stock(product.id, quantity=500.0, unit="g")

        resp = await client.patch(
            "/api/v1/items/adjust",
            json={
                "product_reference_id": str(product.id),
                "location": "fridge",
                "delta": -200.0,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["qty"] == 300.0

    async def test_zero_delta_rejected(self, client, make_product, make_stock):
        product = await make_product(name="Salt", package_quantity=500, package_unit="g")
        await make_stock(product.id, quantity=500.0, unit="g")

        resp = await client.patch(
            "/api/v1/items/adjust",
            json={
                "product_reference_id": str(product.id),
                "location": "fridge",
                "delta": 0,
            },
        )
        assert resp.status_code == 400

    async def test_deplete_item(self, client, make_product, make_stock):
        product = await make_product(name="Butter", package_quantity=227, package_unit="g")
        await make_stock(product.id, quantity=227.0, unit="g")

        resp = await client.patch(
            "/api/v1/items/adjust",
            json={
                "product_reference_id": str(product.id),
                "location": "fridge",
                "delta": -227.0,
            },
        )
        # Item depleted — returns 404
        assert resp.status_code == 404

    async def test_negative_delta_not_found(self, client):
        resp = await client.patch(
            "/api/v1/items/adjust",
            json={
                "product_reference_id": str(uuid.uuid4()),
                "location": "fridge",
                "delta": -100.0,
            },
        )
        assert resp.status_code == 404


class TestMoveItem:
    async def test_move_between_locations(self, client, make_product, make_stock):
        from models.item import Locations

        product = await make_product(name="Chicken", package_quantity=500, package_unit="g")
        await make_stock(product.id, Locations.FRIDGE, 500.0, "g")

        resp = await client.post(
            "/api/v1/items/move",
            json={
                "product_reference_id": str(product.id),
                "from_location": "fridge",
                "to_location": "freezer",
                "quantity": 300.0,
            },
        )
        assert resp.status_code == 200
        # Returns the destination item
        assert resp.json()["location"] == "freezer"
        assert resp.json()["qty"] == 300.0

    async def test_move_not_found(self, client):
        resp = await client.post(
            "/api/v1/items/move",
            json={
                "product_reference_id": str(uuid.uuid4()),
                "from_location": "fridge",
                "to_location": "freezer",
                "quantity": 100.0,
            },
        )
        assert resp.status_code == 404


class TestScanUnitConversion:
    """
    Verify that the scan endpoint stores stock in grams/ml, never in raw count
    units when a weight can be derived.

    These tests use direct CRUD + service calls (no barcode lookup mock) to
    exercise the lot-computation path that was broken by 'eggs' not standardizing
    to 'unit'.
    """

    async def test_weight_unit_stored_directly(self, db_session, make_product, make_stock):
        """Product with a real weight unit (g) stores qty in grams — no conversion needed."""
        from crud.stock_lot import get_lots_for_item
        from models.item import Locations

        product = await make_product(name="Icing Sugar", package_quantity=1000, package_unit="g")
        await make_stock(product.id, Locations.CUPBOARD, 1000.0, "g")

        lots = await get_lots_for_item(db_session, product.id, Locations.CUPBOARD)
        assert len(lots) == 1
        assert lots[0].unit == "g"
        assert lots[0].remaining_quantity == 1000.0

    async def test_eggs_via_avg_weight_converts_to_grams(
        self, db_session, make_product, make_ingredient, make_alias, make_stock
    ):
        """
        Product stored with package_unit='eggs' should be converted to grams
        when the linked ingredient has avg_weight_grams set.

        Simulates the Large Eggs scan scenario that was filing as 'eggs' unit.
        """
        from api.services.unit_converter import convert_to_base_unit
        from crud.ingredient_reference import update_avg_weight
        from crud.stock_lot import get_lots_for_item
        from models.item import Locations

        ingredient = await make_ingredient(name="egg")
        await update_avg_weight(db_session, ingredient.id, avg_weight_grams=53.0, weight_source="manual")
        await make_alias("Large eggs", ingredient.id)

        # Simulate what the scan endpoint does after convert_to_base_unit returns "unit"
        conversion = await convert_to_base_unit(12, "eggs", "Large eggs")
        assert conversion["base_unit"] == "unit"  # eggs now standardizes to unit

        # Then the weight lookup kicks in: 12 × 53g = 636g
        weight_per_unit = 53.0
        lot_qty = 12 * weight_per_unit
        lot_unit = "g"

        product = await make_product(name="Large eggs", package_quantity=12, package_unit="eggs")
        await make_stock(product.id, Locations.FRIDGE, lot_qty, lot_unit)

        lots = await get_lots_for_item(db_session, product.id, Locations.FRIDGE)
        assert lots[0].unit == "g"
        assert lots[0].remaining_quantity == 636.0

    async def test_eggs_via_manual_weight_fallback(self, db_session, make_product, make_stock):
        """
        When no avg_weight_grams on the ingredient, get_manual_weight('egg') = 50g
        should be used as fallback.
        """
        from config.fresh_weights import get_manual_weight
        from api.services.unit_converter import convert_to_base_unit
        from crud.stock_lot import get_lots_for_item
        from models.item import Locations

        # Confirm the manual weight entry exists
        assert get_manual_weight("egg") == 50

        conversion = await convert_to_base_unit(6, "eggs", "Large eggs")
        assert conversion["base_unit"] == "unit"

        lot_qty = 6 * get_manual_weight("egg")  # 300g
        product = await make_product(name="Large eggs", package_quantity=6, package_unit="eggs")
        await make_stock(product.id, Locations.FRIDGE, lot_qty, "g")

        lots = await get_lots_for_item(db_session, product.id, Locations.FRIDGE)
        assert lots[0].unit == "g"
        assert lots[0].remaining_quantity == 300.0

    async def test_unresolvable_count_unit_stays_as_unit(self, db_session, make_product, make_stock):
        """
        Product with package_unit='eggs' but no alias/ingredient/manual-weight
        falls back to storing as 'unit' — degraded mode, not a crash.
        """
        from api.services.unit_converter import convert_to_base_unit
        from crud.stock_lot import get_lots_for_item
        from models.item import Locations

        conversion = await convert_to_base_unit(12, "eggs", "Mystery Brand Eggs XL")
        assert conversion["base_unit"] == "unit"

        # No alias exists → weight_per_unit stays None → falls back to unit storage
        product = await make_product(
            name="Mystery Brand Eggs XL", package_quantity=12, package_unit="eggs"
        )
        await make_stock(product.id, Locations.FRIDGE, 12.0, "unit")

        lots = await get_lots_for_item(db_session, product.id, Locations.FRIDGE)
        assert lots[0].unit == "unit"
        assert lots[0].remaining_quantity == 12.0

    async def test_dozen_unit_expands_before_weight_lookup(self):
        """A dozen of something converts to 12 units before weight lookup."""
        from api.services.unit_converter import convert_to_base_unit

        result = await convert_to_base_unit(1.0, "dozen", "Large eggs")
        assert result["base_unit"] == "unit"
        assert result["quantity"] == 12.0


class TestDeleteItem:
    async def test_delete_item(self, client, make_product, make_stock):
        product = await make_product(name="Eggs", package_quantity=12, package_unit="unit")
        await make_stock(product.id, quantity=12.0, unit="unit")

        resp = await client.request(
            "DELETE",
            "/api/v1/items/",
            json={
                "product_reference_id": str(product.id),
                "location": "fridge",
            },
        )
        assert resp.status_code == 204

        items_resp = await client.get("/api/v1/items/")
        assert len(items_resp.json()) == 0

    async def test_delete_not_found(self, client):
        resp = await client.request(
            "DELETE",
            "/api/v1/items/",
            json={
                "product_reference_id": str(uuid.uuid4()),
                "location": "fridge",
            },
        )
        assert resp.status_code == 404

    async def test_delete_last_item_preserves_product_and_aliases(
        self, db_session, make_product, make_ingredient, make_alias, make_stock
    ):
        """
        Deleting the last item referencing a product leaves ProductReference
        and IngredientAlias rows intact (aliases are a persistent learned cache).
        """
        from crud.item import delete_item_by_composite_key
        from crud.product_reference import get_product_by_barcode
        from crud.ingredient_alias import get_alias_by_text
        from models.item import Locations

        ing = await make_ingredient(name="butter")
        product = await make_product(name="Store Butter", package_quantity=227, package_unit="g", barcode="111")
        await make_alias("Store Butter", ing.id)
        await make_stock(product.id, Locations.FRIDGE, 227.0, "g")

        deleted = await delete_item_by_composite_key(db_session, product.id, Locations.FRIDGE)
        assert deleted is True

        # ProductReference and alias are preserved — not cleaned up on item delete
        assert await get_product_by_barcode(db_session, "111") is not None
        assert await get_alias_by_text(db_session, "Store Butter") is not None

    async def test_delete_one_location_preserves_product_at_other(
        self, db_session, make_product, make_ingredient, make_alias, make_stock
    ):
        """
        Deleting an item at one location must NOT remove the ProductReference
        when the same product still exists at another location.
        """
        from crud.item import delete_item_by_composite_key
        from crud.product_reference import get_product_by_barcode
        from crud.ingredient_alias import get_alias_by_text
        from models.item import Locations

        ing = await make_ingredient(name="milk")
        product = await make_product(name="Whole Milk", package_quantity=1000, package_unit="ml", barcode="222")
        await make_alias("Whole Milk", ing.id)
        await make_stock(product.id, Locations.FRIDGE, 1000.0, "ml")
        await make_stock(product.id, Locations.FREEZER, 500.0, "ml")

        deleted = await delete_item_by_composite_key(db_session, product.id, Locations.FRIDGE)
        assert deleted is True

        # Product still referenced by the freezer item — must not be deleted
        assert await get_product_by_barcode(db_session, "222") is not None
        assert await get_alias_by_text(db_session, "Whole Milk") is not None


class TestFIFODeduction:
    async def test_oldest_lot_consumed_first(self, db_session, make_product, make_stock):
        from crud.item import deduct_stock
        from crud.stock_lot import get_lots_for_item
        from models.item import Locations

        product = await make_product(name="Cheese", package_quantity=200, package_unit="g")
        # Add two lots
        await make_stock(product.id, Locations.FRIDGE, 200.0, "g")
        await make_stock(product.id, Locations.FRIDGE, 300.0, "g")

        # Deduct 250g — should consume all of lot 1 (200g) and 50g of lot 2
        await deduct_stock(db_session, product.id, Locations.FRIDGE, 250.0, "g")

        lots = await get_lots_for_item(db_session, product.id, Locations.FRIDGE)
        assert len(lots) == 1  # First lot fully consumed and deleted
        assert lots[0].remaining_quantity == 250.0  # 300 - 50
