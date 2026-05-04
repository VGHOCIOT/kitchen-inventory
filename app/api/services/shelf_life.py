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


def _find_entry(name: str) -> dict | None:
    normalized = name.lower().strip()

    best_match = None
    best_len = 0
    for entry in _ENTRIES:
        candidates = [entry["name"].lower()] + [k.lower() for k in entry.get("keywords", [])]
        for candidate in candidates:
            if candidate in normalized or normalized in candidate:
                if len(candidate) > best_len:
                    best_len = len(candidate)
                    best_match = entry
    if best_match:
        return best_match

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


def estimate_opened_shelf_life_days(name: str, location: Locations) -> int | None:
    """Returns shelf life in days after opening. None if no after-opening data exists."""
    entry = _find_entry(name)
    if not entry:
        return None
    if location == Locations.FREEZER:
        days = entry.get("after_opening_fridge_days")
    elif location == Locations.CUPBOARD:
        days = entry.get("after_opening_pantry_days") or entry.get("after_opening_fridge_days")
    else:
        days = entry.get("after_opening_fridge_days")
    return int(days) if days is not None else None
