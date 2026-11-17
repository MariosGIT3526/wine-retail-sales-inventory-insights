"""Load landing files into Postgres raw tables (raw.inventory, raw.purchases, raw.sales).

- Every column lands as TEXT. Typing and cleanup happen in dbt staging, where they are tested.
- Each file is loaded in one transaction: delete that file's old rows, COPY the new ones, log it.
  Re-running is safe (idempotent), and a changed file replaces its own rows only.
- raw._load_log records every file + its sha256, so unchanged files are skipped.
- New source columns are added automatically (schema drift is logged, not fatal).

Connection: set DATABASE_URL, or the standard PGHOST / PGPORT / PGUSER / PGPASSWORD / PGDATABASE
(+ PGSSLMODE=require for Supabase).
"""
from __future__ import annotations

import csv
import gzip
import io
import logging
import os
import sys
from pathlib import Path

import psycopg
from psycopg import sql

from config import DATASETS, LANDING_DIR
from landing import sha256

log = logging.getLogger("load")

LOG_DDL = """
create schema if not exists raw;
create table if not exists raw._load_log (
    file_name    text primary key,
    dataset      text not null,
    file_sha256  text not null,
    row_count    integer not null,
    loaded_at    timestamptz not null default now()
);
"""


def connect() -> psycopg.Connection:
    url = os.environ.get("DATABASE_URL")
    return psycopg.connect(url) if url else psycopg.connect()  # empty conninfo -> libpq PG* env vars


def read_gz_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        return header, list(reader)


def ensure_table(cur: psycopg.Cursor, table: str, columns: list[str]) -> None:
    cur.execute(sql.SQL("create table if not exists raw.{} (_file_name text not null)").format(sql.Identifier(table)))
    cur.execute(
        "select column_name from information_schema.columns where table_schema = 'raw' and table_name = %s",
        (table,),
    )
    existing = {r[0] for r in cur.fetchall()}
    for col in columns:
        if col not in existing:
            log.warning("raw.%s: adding new column %s", table, col)
            cur.execute(sql.SQL("alter table raw.{} add column {} text").format(sql.Identifier(table), sql.Identifier(col)))


def load_file(conn: psycopg.Connection, dataset: str, path: Path, digest: str) -> int:
    header, rows = read_gz_csv(path)
    with conn.transaction(), conn.cursor() as cur:
        ensure_table(cur, dataset, header)
        cur.execute(sql.SQL("delete from raw.{} where _file_name = %s").format(sql.Identifier(dataset)), (path.name,))
        cols = sql.SQL(", ").join(sql.Identifier(c) for c in ["_file_name", *header])
        with cur.copy(sql.SQL("copy raw.{} ({}) from stdin").format(sql.Identifier(dataset), cols)) as copy:
            for r in rows:
                copy.write_row([path.name, *[v if v != "" else None for v in r]])
        cur.execute(
            """insert into raw._load_log (file_name, dataset, file_sha256, row_count)
               values (%s, %s, %s, %s)
               on conflict (file_name) do update
               set file_sha256 = excluded.file_sha256, row_count = excluded.row_count, loaded_at = now()""",
            (path.name, dataset, digest, len(rows)),
        )
    return len(rows)


def run() -> int:
    with connect() as conn:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute(LOG_DDL)
            cur.execute("select file_name, file_sha256 from raw._load_log")
            loaded = dict(cur.fetchall())

        for dataset in DATASETS:
            for path in sorted((LANDING_DIR / dataset).glob("*.csv.gz")):
                digest = sha256(path)
                if loaded.get(path.name) == digest:
                    continue
                n = load_file(conn, dataset, path, digest)
                log.info("loaded %s (%s rows) into raw.%s", path.name, n, dataset)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    sys.exit(run())
