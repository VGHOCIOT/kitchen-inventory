"""
One-time script to convert the USDA FoodKeeper Excel file to the simplified
JSON format used by app/api/services/shelf_life.py.

Usage (browser-download route — recommended):
    1. Open https://www.fsis.usda.gov/shared/data/EN/FoodKeeper-Data.xls in your
       browser and save it anywhere (e.g. ~/Downloads/FoodKeeper-Data.xls).
    2. pip install xlrd
    3. python scripts/build_foodkeeper_data.py ~/Downloads/FoodKeeper-Data.xls

Usage (auto-download, may be blocked by USDA CDN):
    pip install xlrd requests
    python scripts/build_foodkeeper_data.py

Output: app/config/foodkeeper_data.json (overwrites existing file)
"""

import json
import math
import re
import sys
import tempfile
from pathlib import Path

try:
    import xlrd
except ImportError:
    sys.exit("Missing: pip install xlrd")


XLS_URL = "https://www.fsis.usda.gov/shared/data/EN/FoodKeeper-Data.xls"
OUT_PATH = Path(__file__).parent.parent / "app" / "config" / "foodkeeper_data.json"


def to_days(value, metric: str | None) -> int | None:
    """Convert a FoodKeeper min/max value + metric string to integer days."""
    if value is None or metric is None:
        return None
    metric_lower = str(metric).strip().lower()
    if not metric_lower or metric_lower in ("not recommended", "n/a", "see tips"):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    if "year" in metric_lower:
        return math.ceil(n * 365)
    if "month" in metric_lower:
        return math.ceil(n * 30)
    if "week" in metric_lower:
        return math.ceil(n * 7)
    return math.ceil(n)  # Days


def midpoint(min_val, max_val, metric: str | None) -> int | None:
    """Compute midpoint of a min/max range in days, or the single value if equal."""
    lo = to_days(min_val, metric)
    hi = to_days(max_val, metric)
    if lo is None and hi is None:
        return None
    if lo is None:
        return hi
    if hi is None:
        return lo
    return math.ceil((lo + hi) / 2)


def normalize_keywords(keywords_str: str | None) -> list[str]:
    if not keywords_str:
        return []
    parts = re.split(r"[,;]", str(keywords_str))
    seen: set[str] = set()
    result = []
    for p in parts:
        kw = p.strip().lower()
        if kw and kw not in seen:
            seen.add(kw)
            result.append(kw)
    return result


def download_xls() -> bytes:
    print(f"Downloading {XLS_URL} …")
    r = requests.get(XLS_URL, timeout=30)
    r.raise_for_status()
    print(f"  Downloaded {len(r.content):,} bytes")
    return r.content


def parse_sheet(sheet) -> list[dict]:
    """Parse the main product sheet into a list of row dicts keyed by header name."""
    headers = [str(cell.value).strip() if cell.value else "" for cell in sheet.row(0)]
    rows = []
    for row_idx in range(1, sheet.nrows):
        row = sheet.row(row_idx)
        row_dict = {}
        for col_idx, cell in enumerate(row):
            key = headers[col_idx]
            val = cell.value
            # xlrd returns floats for numeric cells; convert whole numbers to int
            if isinstance(val, float) and val == int(val):
                val = int(val)
            row_dict[key] = val if val != "" else None
        rows.append(row_dict)
    return rows


def find_product_sheet(book: xlrd.Book):
    """Find the sheet that contains the product/food data (not category or tips sheets)."""
    for i in range(book.nsheets):
        sheet = book.sheet_by_index(i)
        if sheet.nrows < 5:
            continue
        headers = [str(c.value).strip().lower() for c in sheet.row(0)]
        # The product sheet has Name and DOP fields
        if "name" in headers and any("dop" in h for h in headers):
            print(f"  Using sheet: '{sheet.name}' ({sheet.nrows} rows)")
            return sheet
    # Fall back to the largest sheet
    largest = max(range(book.nsheets), key=lambda i: book.sheet_by_index(i).nrows)
    sheet = book.sheet_by_index(largest)
    print(f"  Falling back to largest sheet: '{sheet.name}' ({sheet.nrows} rows)")
    return sheet


def convert_row(row: dict) -> dict | None:
    name = str(row.get("Name") or "").strip()
    if not name:
        return None

    subtitle = str(row.get("Name_subtitle") or "").strip()
    full_name = f"{name}, {subtitle}" if subtitle else name

    keywords = normalize_keywords(row.get("Keywords"))

    dop_fridge = midpoint(
        row.get("DOP_Refrigerate_Min"),
        row.get("DOP_Refrigerate_Max"),
        row.get("DOP_Refrigerate_Metric"),
    )
    dop_freezer = midpoint(
        row.get("DOP_Freeze_Min"),
        row.get("DOP_Freeze_Max"),
        row.get("DOP_Freeze_Metric"),
    )
    dop_pantry = midpoint(
        row.get("DOP_Pantry_Min"),
        row.get("DOP_Pantry_Max"),
        row.get("DOP_Pantry_Metric"),
    )
    after_opening_fridge = midpoint(
        row.get("Refrigerate_After_Opening_Min"),
        row.get("Refrigerate_After_Opening_Max"),
        row.get("Refrigerate_After_Opening_Metric"),
    )
    after_opening_pantry = midpoint(
        row.get("Pantry_After_Opening_Min"),
        row.get("Pantry_After_Opening_Max"),
        row.get("Pantry_After_Opening_Metric"),
    )

    # Skip entries where every shelf-life value is null (useless for lookup)
    if all(v is None for v in [dop_fridge, dop_freezer, dop_pantry, after_opening_fridge, after_opening_pantry]):
        return None

    return {
        "name": full_name,
        "keywords": keywords,
        "dop_fridge_days": dop_fridge,
        "dop_freezer_days": dop_freezer,
        "dop_pantry_days": dop_pantry,
        "after_opening_fridge_days": after_opening_fridge,
        "after_opening_pantry_days": after_opening_pantry,
    }


def main():
    if len(sys.argv) > 1:
        tmp_path = sys.argv[1]
        print(f"Using local file: {tmp_path}")
    else:
        try:
            import requests
        except ImportError:
            sys.exit(
                "Missing: pip install requests\n"
                "Or download the file manually and pass its path as an argument:\n"
                "  python scripts/build_foodkeeper_data.py ~/Downloads/FoodKeeper-Data.xls"
            )
        xls_bytes = download_xls()
        tmp = tempfile.NamedTemporaryFile(suffix=".xls", delete=False)
        tmp.write(xls_bytes)
        tmp.close()
        tmp_path = tmp.name

    print("Parsing Excel …")
    book = xlrd.open_workbook(tmp_path)
    sheet = find_product_sheet(book)
    raw_rows = parse_sheet(sheet)
    print(f"  {len(raw_rows)} raw rows")

    entries = []
    skipped = 0
    for row in raw_rows:
        entry = convert_row(row)
        if entry:
            entries.append(entry)
        else:
            skipped += 1

    entries.sort(key=lambda e: e["name"].lower())

    OUT_PATH.write_text(json.dumps(entries, indent=2))
    print(f"\nWrote {len(entries)} entries to {OUT_PATH}  ({skipped} skipped)")

    # Print a few samples
    print("\nSample entries:")
    samples = [e for e in entries if any(k in e["name"].lower() for k in ["chicken", "milk", "ketchup", "salmon"])][:5]
    for s in samples:
        print(f"  {s['name']}: fridge={s['dop_fridge_days']}d, after_open={s['after_opening_fridge_days']}d")


if __name__ == "__main__":
    main()
