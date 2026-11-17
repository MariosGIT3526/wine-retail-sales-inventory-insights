"""Shared settings for the extract and load steps."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LANDING_DIR = REPO_ROOT / "landing"
STATE_FILE = LANDING_DIR / "_state.json"

# Montgomery County, MD open-data portal (Socrata). Overridable for local tests.
SOCRATA_DOMAIN = os.environ.get("SOCRATA_DOMAIN", "https://data.montgomerycountymd.gov")
SOCRATA_APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "")

PAGE_SIZE = int(os.environ.get("SOCRATA_PAGE_SIZE", 50_000))  # rows per request
REQUEST_TIMEOUT = 120       # seconds
LOCAL_TZ = "America/New_York"  # the county's time zone; snapshot dates use it

# How each source behaves upstream decides how we land it.
#   daily_snapshot   - upstream is OVERWRITTEN daily -> keep one dated file per day (irreplaceable history)
#   monthly_period   - upstream is OVERWRITTEN monthly -> keep one file per purchase month
#   cumulative       - upstream is APPENDED -> keep only the latest full copy (re-pullable, not committed)
DATASETS = {
    "inventory": {
        "id": "ib5t-5ncy",
        "title": "ABS Store Inventory and Sale Items",
        "mode": "daily_snapshot",
        "required_columns": ["code", "totalinventory", "price"],
    },
    "purchases": {
        "id": "kpfd-c5d5",
        "title": "Product Purchases by DLC",
        "mode": "monthly_period",
        "required_columns": ["calendar_year", "calendar_month", "item", "quantity"],
    },
    "sales": {
        "id": "v76h-r7br",
        "title": "Warehouse and Retail Sales",
        "mode": "cumulative",
        "required_columns": ["calendar_year", "cal_month_num", "item_code", "rtl_sales"],
    },
}

# Metadata columns added to every landed row (prefixed with _ so they never clash with source columns).
META_COLUMNS = ["_source_dataset", "_source_updated_at", "_extracted_at", "_extract_method", "_snapshot_date"]

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
