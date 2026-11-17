"""Write landing files: gzipped CSV, deterministic bytes, one file per day/period."""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

from config import LANDING_DIR, META_COLUMNS, MONTHS, STATE_FILE


def write_csv_gz(path: Path, header: list[str], rows: list[list[str]]) -> bool:
    """Write rows to path. Returns True if the file changed.

    gzip mtime is fixed at 0 so identical data produces identical bytes,
    which means git sees no change on days the county didn't change anything.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    raw = gzip.compress(buf.getvalue().encode("utf-8"), compresslevel=9, mtime=0)
    if path.exists() and path.read_bytes() == raw:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return True


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_meta(header: list[str], rows: list[list[str]], meta: dict) -> tuple[list[str], list[list[str]]]:
    """Append the _meta columns (same values on every row)."""
    values = [meta.get(c, "") for c in META_COLUMNS]
    return header + META_COLUMNS, [r + values for r in rows]


def month_number(month_text: str) -> int:
    key = str(month_text).strip().lower()
    if key.isdigit():
        return int(key)
    if key not in MONTHS:
        raise ValueError(f"Unrecognised month: {month_text!r}")
    return MONTHS[key]


def land(dataset: str, mode: str, header: list[str], rows: list[list[str]], snapshot_date: str) -> list[Path]:
    """Route rows to the right landing file(s). Returns the files that changed."""
    out_dir = LANDING_DIR / dataset
    changed: list[Path] = []

    if mode == "daily_snapshot":
        path = out_dir / f"{dataset}_{snapshot_date}.csv.gz"
        if write_csv_gz(path, header, rows):
            changed.append(path)

    elif mode == "monthly_period":
        # One file per purchase month found in the data (normally exactly one).
        yi, mi = header.index("calendar_year"), header.index("calendar_month")
        groups: dict[str, list[list[str]]] = {}
        for r in rows:
            period = f"{int(float(r[yi])):04d}-{month_number(r[mi]):02d}"
            groups.setdefault(period, []).append(r)
        for period, group in sorted(groups.items()):
            path = out_dir / f"{dataset}_{period}.csv.gz"
            if write_csv_gz(path, header, group):
                changed.append(path)

    elif mode == "cumulative":
        path = out_dir / f"{dataset}_latest.csv.gz"
        if write_csv_gz(path, header, rows):
            changed.append(path)

    else:
        raise ValueError(f"Unknown mode {mode}")
    return changed


def read_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def write_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
