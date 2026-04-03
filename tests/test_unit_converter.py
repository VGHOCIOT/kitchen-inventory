"""Tests for the unit conversion service — pure functions, no DB needed."""

from api.services.unit_converter import (
    standardize_unit,
    convert_to_base_unit,
    is_likely_liquid,
    get_unit_dimension,
    can_convert_units,
)


# ── standardize_unit ──────────────────────────────────────────────────────────

class TestStandardizeUnit:
    def test_weight_variants(self):
        for variant in ["g", "gr", "gram", "grams"]:
            assert standardize_unit(variant) == "g"

    def test_kg_variants(self):
        for variant in ["kg", "kilo", "kilogram"]:
            assert standardize_unit(variant) == "kg"

    def test_oz_variants(self):
        for variant in ["oz", "ounce", "ounces"]:
            assert standardize_unit(variant) == "oz"

    def test_lb_variants(self):
        for variant in ["lb", "lbs", "pound", "pounds"]:
            assert standardize_unit(variant) == "lb"

    def test_volume_cup_variants(self):
        for variant in ["cup", "cups", "c"]:
            assert standardize_unit(variant) == "cup"

    def test_volume_tbsp_variants(self):
        for variant in ["tbsp", "tablespoon", "tablespoons"]:
            assert standardize_unit(variant) == "tbsp"

    def test_volume_tsp_variants(self):
        for variant in ["tsp", "teaspoon", "teaspoons"]:
            assert standardize_unit(variant) == "tsp"

    def test_discrete_variants(self):
        for variant in ["unit", "piece", "pieces", "clove", "medium", "large", "small", "whole"]:
            assert standardize_unit(variant) == "unit"

    def test_egg_variants_are_discrete(self):
        """'eggs'/'egg' must standardize to 'unit' — regression for barcode scan bug."""
        for variant in ["egg", "eggs", "Eggs", "EGGS"]:
            assert standardize_unit(variant) == "unit"

    def test_empty_and_none(self):
        assert standardize_unit("") == "unit"
        assert standardize_unit(None) == "unit"

    def test_dozen(self):
        for variant in ["dozen", "doz"]:
            assert standardize_unit(variant) == "dozen"


# ── convert_to_base_unit ──────────────────────────────────────────────────────

class TestConvertToBaseUnit:
    async def test_weight_kg_to_grams(self):
        result = await convert_to_base_unit(1.0, "kg")
        assert result["quantity"] == 1000.0
        assert result["base_unit"] == "g"
        assert result["conversion_confidence"] == "high"

    async def test_weight_oz_to_grams(self):
        result = await convert_to_base_unit(1.0, "oz")
        assert result["quantity"] == 28.35
        assert result["base_unit"] == "g"

    async def test_weight_lb_to_grams(self):
        result = await convert_to_base_unit(1.0, "lb")
        assert abs(result["quantity"] - 453.59) < 0.01
        assert result["base_unit"] == "g"

    async def test_volume_cup_to_ml(self):
        result = await convert_to_base_unit(1.0, "cup")
        assert result["quantity"] == 240.0
        assert result["base_unit"] == "ml"

    async def test_volume_tbsp_to_ml(self):
        result = await convert_to_base_unit(1.0, "tbsp")
        assert result["quantity"] == 14.79
        assert result["base_unit"] == "ml"

    async def test_cup_flour_to_grams(self):
        """Known dry ingredient uses density table."""
        result = await convert_to_base_unit(1.0, "cup", "flour")
        assert result["quantity"] == 120.0
        assert result["base_unit"] == "g"
        assert result["conversion_confidence"] == "high"

    async def test_cup_milk_stays_ml(self):
        """Known liquid stays as ml."""
        result = await convert_to_base_unit(1.0, "cup", "milk")
        assert result["quantity"] == 240.0
        assert result["base_unit"] == "ml"

    async def test_dozen_to_units(self):
        result = await convert_to_base_unit(1.0, "dozen")
        assert result["quantity"] == 12.0
        assert result["base_unit"] == "unit"

    async def test_discrete_unit(self):
        result = await convert_to_base_unit(2.0, "piece")
        assert result["quantity"] == 2.0
        assert result["base_unit"] == "unit"

    async def test_empty_unit(self):
        result = await convert_to_base_unit(3.0, "")
        assert result["quantity"] == 3.0
        assert result["base_unit"] == "unit"

    async def test_none_unit(self):
        result = await convert_to_base_unit(3.0, None)
        assert result["quantity"] == 3.0
        assert result["base_unit"] == "unit"

    async def test_cup_unknown_liquid_by_name(self):
        """Unknown ingredient with liquid keyword → ml."""
        result = await convert_to_base_unit(1.0, "cup", "chicken broth")
        assert result["base_unit"] == "ml"
        assert result["conversion_confidence"] == "medium"

    async def test_cup_unknown_dry(self):
        """Unknown dry ingredient uses default density."""
        result = await convert_to_base_unit(1.0, "cup", "mystery powder")
        assert result["base_unit"] == "g"
        assert result["conversion_confidence"] == "medium"

    async def test_eggs_unit_returns_unit(self):
        """'eggs' as a unit must return base_unit='unit', not pass through as 'eggs'."""
        result = await convert_to_base_unit(12.0, "eggs", "Large eggs")
        assert result["base_unit"] == "unit"
        assert result["quantity"] == 12.0

    async def test_unrecognized_unit_passthrough(self):
        """Truly unrecognized units pass through with low confidence — not silently treated as count."""
        result = await convert_to_base_unit(1.0, "flurble", "something")
        assert result["base_unit"] == "flurble"
        assert result["conversion_confidence"] == "low"


# ── is_likely_liquid ──────────────────────────────────────────────────────────

class TestIsLikelyLiquid:
    def test_oil(self):
        assert is_likely_liquid("olive oil") is True

    def test_broth(self):
        assert is_likely_liquid("chicken broth") is True

    def test_flour(self):
        assert is_likely_liquid("flour") is False

    def test_none(self):
        assert is_likely_liquid(None) is False


# ── get_unit_dimension ────────────────────────────────────────────────────────

class TestGetUnitDimension:
    def test_weight(self):
        assert get_unit_dimension("g") == "weight"
        assert get_unit_dimension("kg") == "weight"

    def test_volume(self):
        assert get_unit_dimension("ml") == "volume"
        assert get_unit_dimension("cup") == "volume"

    def test_count(self):
        assert get_unit_dimension("unit") == "count"
        assert get_unit_dimension("") == "count"

    def test_unknown(self):
        assert get_unit_dimension("xyz") == "unknown"


# ── can_convert_units ─────────────────────────────────────────────────────────

class TestCanConvertUnits:
    async def test_same_dimension_weight(self):
        assert await can_convert_units("g", "kg") is True

    async def test_same_dimension_volume(self):
        assert await can_convert_units("ml", "cup") is True

    async def test_cross_dimension(self):
        assert await can_convert_units("g", "ml") is False

    async def test_same_unit(self):
        assert await can_convert_units("g", "g") is True

    async def test_discrete_units(self):
        assert await can_convert_units("unit", "dozen") is True
