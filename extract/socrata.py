"""Minimal Socrata (SODA 2.x) client: metadata, paged CSV pulls, retries, app token."""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import PAGE_SIZE, REQUEST_TIMEOUT, SOCRATA_APP_TOKEN, SOCRATA_DOMAIN

log = logging.getLogger(__name__)


class SocrataClient:
    def __init__(self, domain: str = SOCRATA_DOMAIN, app_token: str = SOCRATA_APP_TOKEN):
        self.domain = domain.rstrip("/")
        self.session = requests.Session()
        # Retry transient failures with exponential backoff: 2s, 4s, 8s, 16s, 32s.
        retry = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        if app_token:
            # The app token raises the rate limit; without one, requests are throttled harder.
            self.session.headers["X-App-Token"] = app_token
        else:
            log.warning("SOCRATA_APP_TOKEN is not set - requests will be throttled more aggressively.")

    def get_metadata(self, dataset_id: str) -> dict:
        """Dataset metadata. rowsUpdatedAt tells us when the county last changed the data."""
        resp = self.session.get(f"{self.domain}/api/views/{dataset_id}.json", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        meta = resp.json()
        rows_updated = meta.get("rowsUpdatedAt")
        return {
            "name": meta.get("name"),
            "rows_updated_at": datetime.fromtimestamp(rows_updated, tz=timezone.utc) if rows_updated else None,
            "columns": [c["fieldName"] for c in meta.get("columns", []) if not c["fieldName"].startswith(":")],
        }

    def fetch_all(self, dataset_id: str) -> tuple[list[str], list[list[str]]]:
        """Pull every row as CSV, PAGE_SIZE rows at a time, in a stable order (:id) so pages don't overlap."""
        header: list[str] | None = None
        rows: list[list[str]] = []
        offset = 0
        while True:
            resp = self.session.get(
                f"{self.domain}/resource/{dataset_id}.csv",
                params={"$limit": PAGE_SIZE, "$offset": offset, "$order": ":id"},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            reader = csv.reader(io.StringIO(resp.content.decode("utf-8")))
            page_header = next(reader, None)
            page = list(reader)
            if header is None:
                header = page_header
            elif page_header and page_header != header:
                raise RuntimeError(f"{dataset_id}: column list changed between pages")
            rows.extend(page)
            log.info("%s: fetched %s rows (offset %s)", dataset_id, len(page), offset)
            if len(page) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        return header or [], rows
