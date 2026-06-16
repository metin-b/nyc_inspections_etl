"""Functions for retrieving raw inspection data from the API."""
from __future__ import annotations
from pathlib import Path
from typing import Iterator
import requests
from .config import Config
import time
import json
from datetime import datetime, timezone


def make_session(cfg: Config) -> requests.Session:
    """Return a requests.Session. If cfg.app_token is set, attach it (header or param)."""
    session = requests.Session()

    if cfg.app_token:
        session.headers.update({'X-App-Token': cfg.app_token})

    return session


def fetch_page(session: requests.Session, cfg: Config, *, offset: int, where: str | None = None) -> list[dict]:
    """Fetch a single page of inspection records from the API.

    Must handle transport failure: timeout, retry transient errors (incl. HTTP 429)
    with exponential backoff, give up after N attempts. Returns the page as a list of dicts.
    """


    params = {
        '$limit': cfg.page_size,
        '$offset': offset,
        '$order': cfg.order,
    }
    if where:
        params['$where'] = where


    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(cfg.endpoint, params=params, timeout=30)

            if response.status_code == 429 or 500 <= response.status_code <= 599:
                if attempt < max_attempts:
                    wait_seconds = 2 ** attempt
                    time.sleep(wait_seconds)
                    continue

            response.raise_for_status()
            return response.json()

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < max_attempts:
                wait_seconds = 2 ** attempt
                time.sleep(wait_seconds)
                continue

    raise  RuntimeError(f'Failed to fetch page after {max_attempts} attempts. Offset={offset}')


def extract_all(session: requests.Session, cfg: Config, *, where: str | None = None) -> Iterator[dict]:
    """Yield records from all available API pages."""
    offset = 0
    while True:
        page = fetch_page(session, cfg, offset=offset, where=where)
        for record in page:
            yield record
        if len(page) < cfg.page_size:
            break
        offset += cfg.page_size


def land_raw(records: list[dict], cfg: Config) -> Path:
    """Save the raw API response to disk and return its path."""
    cfg.raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    path = cfg.raw_dir / f'nyc_inspections_raw_{timestamp}.json'

    with path.open('w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    return path

def build_where_clause(watermark: datetime | None) -> str | None:
    """Build a Socrata $where clause for incremental extraction"""
    if watermark is None:
        return None

    watermark_text = watermark.isoformat()
    return f"record_date > '{watermark_text}'"


