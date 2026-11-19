"""Pull the three ABS datasets from Socrata into landing/.

Usage:
    python extract/extract.py                 # all datasets, skip ones the county hasn't changed
    python extract/extract.py --only inventory
    python extract/extract.py --force         # re-pull even if unchanged

A dataset is skipped when its rowsUpdatedAt matches the last pull (stored in landing/_state.json).
That keeps the daily job cheap and means _source_updated_at always reflects a real county update,
which is what the dbt freshness check reads.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import DATASETS, LANDING_DIR, LOCAL_TZ
from landing import add_meta, land, read_state, write_state
from socrata import SocrataClient

log = logging.getLogger("extract")


def validate(dataset: str, header: list[str], rows: list[list[str]], required: list[str]) -> None:
    """Fail loudly instead of landing a broken file."""
    missing = [c for c in required if c not in header]
    if missing:
        raise RuntimeError(f"{dataset}: expected columns missing from source: {missing}")
    if not rows:
        raise RuntimeError(f"{dataset}: source returned 0 rows")


def run(only: list[str] | None, force: bool) -> int:
    client = SocrataClient()
    state = read_state()
    failures = 0

    for name, cfg in DATASETS.items():
        if only and name not in only:
            continue
        try:
            meta = client.get_metadata(cfg["id"])
            updated = meta["rows_updated_at"]
            updated_iso = updated.isoformat() if updated else ""
            landed_here = cfg["mode"] != "cumulative" or (LANDING_DIR / name / f"{name}_latest.csv.gz").exists()
            if not force and landed_here and updated_iso and state.get(name, {}).get("rows_updated_at") == updated_iso:
                log.info("%s: unchanged since %s - skipping", name, updated_iso)
                continue

            header, rows = client.fetch_all(cfg["id"])
            validate(name, header, rows, cfg["required_columns"])

            # Snapshot date = the county's update date in local time, not our run date.
            ref = updated or datetime.now(timezone.utc)
            snapshot_date = ref.astimezone(ZoneInfo(LOCAL_TZ)).date().isoformat()
            header, rows = add_meta(header, rows, {
                "_source_dataset": cfg["id"],
                "_source_updated_at": updated_iso,
                "_extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "_extract_method": "api",
                "_snapshot_date": snapshot_date if cfg["mode"] == "daily_snapshot" else "",
            })
            changed = land(name, cfg["mode"], header, rows, snapshot_date)
            log.info("%s: %s rows, county updated %s, files changed: %s",
                     name, len(rows), updated_iso, [p.name for p in changed] or "none")
            state[name] = {"rows_updated_at": updated_iso, "row_count": len(rows)}
        except Exception:  # keep going so one bad dataset doesn't block the others
            failures += 1
            log.exception("%s: extract failed", name)

    write_state(state)
    return 1 if failures else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--only", nargs="*", choices=list(DATASETS))
    p.add_argument("--force", action="store_true")
    a = p.parse_args()
    sys.exit(run(a.only, a.force))
