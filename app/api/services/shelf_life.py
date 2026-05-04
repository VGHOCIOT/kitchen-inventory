import json
import difflib
from pathlib import Path

from models.item import Locations

_DATA_PATH = Path(__file__).parent.parent.parent / "config" / "foodkeeper_data.json"

with _DATA_PATH.open() as _f:
    _ENTRIES: list[dict] = json.load(_f)

_SEARCH_STRINGS: list[str] = []
_SEARCH_INDEX: list[int] = []

for _i, _entry in enumerate(_ENTRIES):
    _SEARCH_STRINGS.append(_entry["name"].lower())
    _SEARCH_INDEX.append(_i)
    for _kw in _entry.get("keywords", []):
        _kw_lower = _kw.lower().strip()
        if _kw_lower and _kw_lower not in _SEARCH_STRINGS:
            _SEARCH_STRINGS.append(_kw_lower)
            _SEARCH_INDEX.append(_i)

_LOCATION_DEFAULTS = {
    Locations.FRIDGE: 7,
    Locations.FREEZER: 180,
    Locations.CUPBOARD: 30,
}

# Ordered by specificity — first match wins. Keywords are checked against each
# category string after stripping the "en:" prefix and lowercasing.
_CATEGORY_OPENED_FALLBACK: list[tuple[str, dict[Locations, int]]] = [
    ("sausage",     {Locations.FRIDGE: 5,  Locations.FREEZER: 60}),
    ("deli-meat",   {Locations.FRIDGE: 5}),
    ("smoked-meat", {Locations.FRIDGE: 7}),
    ("cured-meat",  {Locations.FRIDGE: 7}),
    ("deli",        {Locations.FRIDGE: 5}),
    ("poultry",     {Locations.FRIDGE: 3,  Locations.FREEZER: 90}),
    ("meat",        {Locations.FRIDGE: 3,  Locations.FREEZER: 90}),
    ("seafood",     {Locations.FRIDGE: 2,  Locations.FREEZER: 90}),
    ("fish",        {Locations.FRIDGE: 2,  Locations.FREEZER: 90}),
    ("cheese",      {Locations.FRIDGE: 14}),
    ("dairy",       {Locations.FRIDGE: 7,  Locations.CUPBOARD: 1}),
    ("milk",        {Locations.FRIDGE: 7}),
    ("oil",         {Locations.CUPBOARD: 90, Locations.FRIDGE: 180}),
    ("spread",      {Locations.FRIDGE: 21, Locations.CUPBOARD: 14}),
    ("jam",         {Locations.FRIDGE: 90, Locations.CUPBOARD: 30}),
    ("pickle",      {Locations.FRIDGE: 90}),
    ("condiment",   {Locations.FRIDGE: 30, Locations.CUPBOARD: 90}),
    ("sauce",       {Locations.FRIDGE: 14, Locations.CUPBOARD: 30}),
    ("canned",      {Locations.FRIDGE: 5,  Locations.CUPBOARD: 5}),
    ("beverage",    {Locations.FRIDGE: 5,  Locations.CUPBOARD: 3}),
    ("drink",       {Locations.FRIDGE: 5,  Locations.CUPBOARD: 3}),
    ("bread",       {Locations.CUPBOARD: 5, Locations.FRIDGE: 14}),
    ("cereal",      {Locations.CUPBOARD: 30}),
    ("pasta",       {Locations.CUPBOARD: 365}),
    ("spice",       {Locations.CUPBOARD: 365}),
    ("snack",       {Locations.CUPBOARD: 14}),
    ("frozen",      {Locations.FREEZER: 30}),
]


def _opened_days_from_categories(categories: list[str], location: Locations) -> int | None:
    if location == Locations.FREEZER:
        return None
    normalised = [c.lower().removeprefix("en:") for c in categories]
    for keyword, loc_map in _CATEGORY_OPENED_FALLBACK:
        if any(keyword in cat for cat in normalised):
            return loc_map.get(location)
    return None


def _find_entry(name: str) -> dict | None:
    normalized = name.lower().strip()

    best_match = None
    best_len = 0
    fallback_match = None
    fallback_len = 0
    for entry in _ENTRIES:
        candidates = [entry["name"].lower()] + [k.lower() for k in entry.get("keywords", [])]
        for candidate in candidates:
            if candidate in normalized:
                if len(candidate) > best_len:
                    best_len = len(candidate)
                    best_match = entry
            elif normalized in candidate:
                if len(candidate) > fallback_len:
                    fallback_len = len(candidate)
                    fallback_match = entry
    if best_match:
        return best_match
    if fallback_match:
        return fallback_match

    matches = difflib.get_close_matches(normalized, _SEARCH_STRINGS, n=1, cutoff=0.7)
    if matches:
        idx = _SEARCH_STRINGS.index(matches[0])
        return _ENTRIES[_SEARCH_INDEX[idx]]

    return None


def estimate_shelf_life_days(name: str, location: Locations) -> int:
    """Returns DOP-based shelf life in days for a sealed item at the given location."""
    entry = _find_entry(name)
    if entry:
        if location == Locations.FRIDGE:
            days = entry.get("dop_fridge_days")
        elif location == Locations.FREEZER:
            days = entry.get("dop_freezer_days")
        else:
            days = entry.get("dop_pantry_days")
        if days is not None:
            return int(days)
    return _LOCATION_DEFAULTS[location]


def estimate_opened_shelf_life_days(
    name: str,
    location: Locations,
    categories: list[str] | None = None,
) -> int | None:
    """Returns shelf life in days after opening.

    Resolution order:
    1. Specific foodkeeper entry for the item name.
    2. Category-based fallback using _CATEGORY_OPENED_FALLBACK.
    3. None — caller decides what to do (e.g. keep existing expiry).
    """
    if location == Locations.FREEZER:
        return None

    entry = _find_entry(name)
    if entry:
        if location == Locations.CUPBOARD:
            days = entry.get("after_opening_pantry_days") or entry.get("after_opening_fridge_days")
        else:
            days = entry.get("after_opening_fridge_days")
        if days is not None:
            return int(days)

    if categories:
        return _opened_days_from_categories(categories, location)

    return None
