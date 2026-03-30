"""Tests for seed functions (aliases and substitutions)."""

from sqlalchemy import select, func


class TestSeedAliases:
    async def test_creates_data(self, db_session):
        from db.seed import seed_aliases
        from models.ingredient_alias import IngredientAlias

        result = await seed_aliases(db_session)
        assert result["aliases_created"] > 0

        count = await db_session.execute(select(func.count(IngredientAlias.id)))
        assert count.scalar() > 0

    async def test_idempotent(self, db_session):
        from db.seed import seed_aliases

        result1 = await seed_aliases(db_session)
        assert result1["aliases_created"] > 0

        result2 = await seed_aliases(db_session)
        assert result2["aliases_created"] == 0
        assert result2["skipped"] > 0


class TestSeedSubstitutions:
    async def test_creates_data(self, db_session):
        from db.seed import seed_substitutions
        from models.ingredient_substitution import IngredientSubstitution

        result = await seed_substitutions(db_session)
        assert result["created"] > 0

        count = await db_session.execute(select(func.count(IngredientSubstitution.id)))
        assert count.scalar() > 0

    async def test_idempotent(self, db_session):
        from db.seed import seed_substitutions

        result1 = await seed_substitutions(db_session)
        assert result1["created"] > 0

        result2 = await seed_substitutions(db_session)
        assert result2["created"] == 0
        assert result2["skipped"] > 0

    async def test_bidirectional_creates_reverse(self, db_session):
        from db.seed import seed_substitutions
        from models.ingredient_substitution import IngredientSubstitution
        from crud.ingredient_reference import get_ingredient_by_name

        await seed_substitutions(db_session)

        # "butter" <-> "margarine" is bidirectional in config
        butter = await get_ingredient_by_name(db_session, "butter")
        margarine = await get_ingredient_by_name(db_session, "margarine")

        if butter and margarine:
            # Check forward
            fwd = await db_session.execute(
                select(IngredientSubstitution).where(
                    IngredientSubstitution.original_ingredient_id == butter.id,
                    IngredientSubstitution.substitute_ingredient_id == margarine.id,
                )
            )
            assert fwd.scalar_one_or_none() is not None

            # Check reverse
            rev = await db_session.execute(
                select(IngredientSubstitution).where(
                    IngredientSubstitution.original_ingredient_id == margarine.id,
                    IngredientSubstitution.substitute_ingredient_id == butter.id,
                )
            )
            assert rev.scalar_one_or_none() is not None


class TestRunAllSeeds:
    async def test_runs_both(self, db_session):
        from db.seed import run_all_seeds
        from models.ingredient_alias import IngredientAlias
        from models.ingredient_substitution import IngredientSubstitution

        await run_all_seeds(db_session)

        alias_count = await db_session.execute(select(func.count(IngredientAlias.id)))
        assert alias_count.scalar() > 0

        sub_count = await db_session.execute(select(func.count(IngredientSubstitution.id)))
        assert sub_count.scalar() > 0
