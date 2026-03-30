"""Tests for substitution CRUD endpoints."""

import uuid


class TestListSubstitutions:
    async def test_empty(self, client):
        resp = await client.get("/api/v1/substitutions/")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_after_create(self, client, make_ingredient, make_substitution):
        butter = await make_ingredient(name="butter")
        margarine = await make_ingredient(name="margarine")
        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)

        resp = await client.get("/api/v1/substitutions/")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["original_ingredient_name"] == "butter"
        assert data[0]["substitute_ingredient_name"] == "margarine"
        assert data[0]["ratio"] == 1.0


class TestListForIngredient:
    async def test_returns_matching_only(self, client, make_ingredient, make_substitution):
        butter = await make_ingredient(name="butter")
        margarine = await make_ingredient(name="margarine")
        olive_oil = await make_ingredient(name="olive oil")

        await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)
        await make_substitution(butter.id, olive_oil.id, ratio=0.75, quality_score=6)

        resp = await client.get(f"/api/v1/substitutions/{butter.id}")
        data = resp.json()
        assert len(data) == 2

        resp2 = await client.get(f"/api/v1/substitutions/{margarine.id}")
        assert len(resp2.json()) == 0


class TestCreateSubstitution:
    async def test_create(self, client, make_ingredient):
        lemon = await make_ingredient(name="lemon")
        lime = await make_ingredient(name="lime")

        resp = await client.post(
            "/api/v1/substitutions/",
            json={
                "original_ingredient_id": str(lemon.id),
                "substitute_ingredient_id": str(lime.id),
                "ratio": 1.0,
                "quality_score": 9,
                "notes": "Nearly interchangeable",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["original_ingredient_name"] == "lemon"
        assert data["substitute_ingredient_name"] == "lime"
        assert data["quality_score"] == 9

    async def test_missing_original(self, client, make_ingredient):
        lime = await make_ingredient(name="lime")

        resp = await client.post(
            "/api/v1/substitutions/",
            json={
                "original_ingredient_id": str(uuid.uuid4()),
                "substitute_ingredient_id": str(lime.id),
            },
        )
        assert resp.status_code == 404

    async def test_missing_substitute(self, client, make_ingredient):
        lemon = await make_ingredient(name="lemon")

        resp = await client.post(
            "/api/v1/substitutions/",
            json={
                "original_ingredient_id": str(lemon.id),
                "substitute_ingredient_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 404


class TestDeleteSubstitution:
    async def test_delete(self, client, make_ingredient, make_substitution):
        a = await make_ingredient(name="a")
        b = await make_ingredient(name="b")
        sub = await make_substitution(a.id, b.id)

        resp = await client.delete(f"/api/v1/substitutions/{sub.id}")
        assert resp.status_code == 204

    async def test_delete_not_found(self, client):
        resp = await client.delete(f"/api/v1/substitutions/{uuid.uuid4()}")
        assert resp.status_code == 404
