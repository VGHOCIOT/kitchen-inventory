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
        assert data[0]["qty"] == 500.0

    async def test_by_location(self, client, make_product, make_stock):
        from models.item import Locations

        product = await make_product(name="Milk", package_quantity=1000, package_unit="ml")
        await make_stock(product.id, Locations.FRIDGE, 1000.0, "ml")

        resp = await client.get("/api/v1/items/location/Fridge")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp = await client.get("/api/v1/items/location/Cupboard")
        assert resp.status_code == 200
        assert len(resp.json()) == 0


class TestAddFresh:
    async def test_add_fresh_item(self, client):
        resp = await client.post(
            "/api/v1/items/add-fresh?location=Fridge",
            json={"name": "Bananas", "weight_grams": 300.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["item"]["qty"] == 300.0
        assert data["item"]["unit"] == "g"
        assert data["product_reference"]["name"] == "Bananas"

    async def test_add_fresh_twice_sums_qty(self, client):
        await client.post(
            "/api/v1/items/add-fresh?location=Fridge",
            json={"name": "Apples", "weight_grams": 200.0},
        )
        resp = await client.post(
            "/api/v1/items/add-fresh?location=Fridge",
            json={"name": "Apples", "weight_grams": 150.0},
        )
        assert resp.status_code == 200
        assert resp.json()["item"]["qty"] == 350.0


class TestLotsForItem:
    async def test_list_lots(self, client, make_product, make_stock):
        from models.item import Locations

        product = await make_product(name="Rice", package_quantity=1000, package_unit="g")
        await make_stock(product.id, Locations.CUPBOARD, 500.0, "g")
        await make_stock(product.id, Locations.CUPBOARD, 300.0, "g")

        resp = await client.get(f"/api/v1/items/lots/{product.id}/Cupboard")
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
                "location": "Fridge",
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
                "location": "Fridge",
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
                "location": "Fridge",
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
                "location": "Fridge",
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
                "location": "Fridge",
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
                "from_location": "Fridge",
                "to_location": "Freezer",
                "quantity": 300.0,
            },
        )
        assert resp.status_code == 200
        # Returns the destination item
        assert resp.json()["location"] == "Freezer"
        assert resp.json()["qty"] == 300.0

    async def test_move_not_found(self, client):
        resp = await client.post(
            "/api/v1/items/move",
            json={
                "product_reference_id": str(uuid.uuid4()),
                "from_location": "Fridge",
                "to_location": "Freezer",
                "quantity": 100.0,
            },
        )
        assert resp.status_code == 404


class TestDeleteItem:
    async def test_delete_item(self, client, make_product, make_stock):
        product = await make_product(name="Eggs", package_quantity=12, package_unit="unit")
        await make_stock(product.id, quantity=12.0, unit="unit")

        resp = await client.request(
            "DELETE",
            "/api/v1/items/",
            json={
                "product_reference_id": str(product.id),
                "location": "Fridge",
            },
        )
        assert resp.status_code == 204

        # Verify it's gone
        items_resp = await client.get("/api/v1/items/")
        assert len(items_resp.json()) == 0

    async def test_delete_not_found(self, client):
        resp = await client.request(
            "DELETE",
            "/api/v1/items/",
            json={
                "product_reference_id": str(uuid.uuid4()),
                "location": "Fridge",
            },
        )
        assert resp.status_code == 404


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
