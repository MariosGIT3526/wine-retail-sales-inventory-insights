"""Turn a CSV downloaded by hand from the county portal into a landing file.

Why: the portal OVERWRITES inventory daily and purchases monthly. Any CSV you already downloaded
is the only copy of that day/month left anywhere, so it is worth keeping.

Portal "Export" CSVs use display names ("Total Inventory") and display formatting ("$17.99",
"1,035.00", "10/31/2026"). This script renames columns to the API field names and leaves the
values as-is; dbt staging handles both formats. Rows are tagged _extract_method = 'manual_export'.

Examples:
    python extract/backfill_from_csv.py inventory data/manual_exports/inventory_export_2026-10-08.csv --snapshot-date 2026-10-08
    python extract/backfill_from_csv.py purchases data/manual_exports/purchases_export_2026-10-08.csv
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from config import DATASETS
from landing import add_meta, land

# Portal display name -> API fieldName (from each dataset's /api/views/<id>.json)
RENAMES = {
    "inventory": {
        "Code": "code", "Category": "category", "Description": "description", "Size": "size",
        "Total Inventory": "totalinventory", "Price": "price", "Sale Price": "saleprice",
        "Sale End Date": "saleenddate",
    },
    "purchases": {
        "CALENDAR YEAR": "calendar_year", "MONTH": "calendar_month", "VENDOR NAME": "vendor_name",
        "CATEGORY": "inventory_category", "ITEM": "item", "ITEM DESCRIPTION": "item_description",
        "QUANTITY": "quantity", "TRANSACTION SOURCE TYPE": "transaction_source_type_name",
    },
    "sales": {
        "YEAR": "calendar_year", "MONTH": "cal_month_num", "SUPPLIER": "supplier", "ITEM CODE": "item_code",
        "ITEM DESCRIPTION": "item_description", "ITEM TYPE": "item_type", "RETAIL SALES": "rtl_sales",
        "RETAIL TRANSFERS": "rtl_transfers", "WAREHOUSE SALES": "whs_sales",
    },
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("dataset", choices=list(RENAMES))
    p.add_argument("csv_path", type=Path)
    p.add_argument("--snapshot-date", help="YYYY-MM-DD the export was downloaded (required for inventory)")
    a = p.parse_args()

    cfg = DATASETS[a.dataset]
    if cfg["mode"] == "daily_snapshot" and not a.snapshot_date:
        p.error("--snapshot-date is required for inventory (the day you downloaded the file)")

    with a.csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        display_header = [h.strip() for h in next(reader)]  # strip() fixes the "ITEM " trailing space
        rows = list(reader)

    mapping = RENAMES[a.dataset]
    unknown = [h for h in display_header if h not in mapping]
    if unknown:
        raise SystemExit(f"Unrecognised columns {unknown} - is this the right dataset?")
    header = [mapping[h] for h in display_header]

    header, rows = add_meta(header, rows, {
        "_source_dataset": cfg["id"],
        "_source_updated_at": f"{a.snapshot_date}T12:00:00+00:00" if a.snapshot_date else "",
        "_extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "_extract_method": "manual_export",
        "_snapshot_date": a.snapshot_date or "",
    })
    changed = land(a.dataset, cfg["mode"], header, rows, a.snapshot_date or "")
    print(f"{len(rows)} rows -> {[str(c) for c in changed] or 'no change'}")


if __name__ == "__main__":
    main()
