# NYC Restaurant Inspections ETL

A Python ETL project that extracts New York City restaurant inspection data from the NYC Open Data (Socrata) API, validates records with Pydantic, cleans and standardizes the data with pandas, and loads the results into a SQLite data warehouse.

The pipeline supports both full refresh and incremental loading using a persisted `record_date` watermark, and is designed so that reruns are idempotent.

## Project Goals

* Extract restaurant inspection records from the public Socrata API.
* Preserve the original API response as a raw ("bronze") JSON dataset.
* Validate incoming records using Pydantic models.
* Apply documented data-quality rules and transformations.
* Produce a clean, consistent dataset ready for analysis and reporting.
* Load the cleaned data into SQLite.
* Support incremental extraction using a persisted watermark.
* Keep reruns idempotent by merging new records with existing warehouse data and removing exact duplicates.

## Data Source

**NYC Open Data – Restaurant Inspection Results**

API endpoint:

```text
https://data.cityofnewyork.us/resource/43nn-pn8j.json
```

Access is unauthenticated. A Socrata application token can optionally be supplied (`Config.app_token`) to raise rate limits; it is sent as an `X-App-Token` header when present.

## Architecture

```text
NYC Open Data API
        │
        ▼
Extract
(pagination + retry/backoff + optional Socrata $where filter)
        │
        ▼
Raw JSON (data/raw)            ← bronze landing, one file per pull
        │
        ▼
Validate (Pydantic)           ← good rows vs. bad rows
        │
        ▼
Transform (pandas)            ← standardize, coerce, clean, derive
        │
        ▼
SQLite Warehouse
(inspections table + etl_state watermark table)
```

## Current Features

* API extraction with offset pagination
* Transient-failure handling: retry with exponential backoff on HTTP 429 / 5xx and on timeouts and connection errors (3 attempts, 30s request timeout)
* Raw JSON landing for reproducible processing (one timestamped file per pull)
* Pydantic schema validation with good/bad record separation
* Column standardization
* Text normalization
* Sentinel value handling
* Type coercion
* Exact duplicate removal
* Derived `is_critical` field
* Incremental extraction via a persisted `record_date` watermark
* Idempotent loads (full refresh replaces; incremental merges + dedupes)

## Quickstart

```bash
pip install -r requirements.txt

# First run: no watermark exists yet, so this performs a full initial extract,
# then loads and records the watermark.
python -m src.cli run

# Subsequent runs: incremental — only records with record_date newer than the
# stored watermark are requested.
python -m src.cli run

# Force a complete refresh (ignores the watermark, replaces the table):
python -m src.cli run --full
```

## CLI Commands

| Command       | Description                                                                  |
| ------------- | ---------------------------------------------------------------------------- |
| `run`         | End-to-end: extract → validate → transform → load → verify (incremental).    |
| `run --full`  | Same pipeline, but full refresh — ignores the watermark and replaces the table. |
| `extract`     | Pull from the API and land raw JSON to `data/raw/` only.                      |
| `transform`   | **Stub** — not yet implemented as a standalone step (see Known Limitations).  |
| `load`        | **Stub** — not yet implemented as a standalone step (see Known Limitations).  |

## Incremental Load & Idempotency

Incremental behavior is driven by a watermark stored in the `etl_state` table:

* After each successful load, the maximum `record_date` in the cleaned data is written to `etl_state` under the key `record_date_watermark`.
* On the next incremental `run`, `build_where_clause()` turns that watermark into a Socrata filter (`record_date > '<watermark>'`), so the API only returns newer records.
* On the very first run (no watermark present), extraction falls back to a full pull.

Reruns are kept idempotent two ways:

* **Full refresh** writes with `if_exists="replace"`, so re-running cannot append duplicate rows.
* **Incremental** reads the existing table, concatenates the new rows, drops exact duplicates, and rewrites the table. If the API returns no new records (an empty page), the table and watermark are left unchanged.

## Validation

Validation uses Pydantic v2 as a schema-on-read gate (`models.InspectionRecord`). `validate_records()` returns a tuple of accepted records and rejected rows (each rejected row carries the original payload plus the validation errors). Date fields are intentionally kept as strings at the validation stage; date parsing happens later in the transform layer with pandas. This keeps validation focused on record shape and basic field compatibility rather than rejecting rows over API datetime formatting.

## Data Quality Rules

The transformation pipeline currently performs the following operations:

* Rename source columns to standardized names.
* Trim leading and trailing whitespace from text fields.
* Convert empty strings to null values.
* Convert placeholder borough value `"0"` to null.
* Convert placeholder latitude/longitude values (`0`) to null.
* Convert `inspection_date` sentinel value `1900-01-01` to null.
* Convert dates and timestamps into appropriate Python/pandas types.
* Convert `score` to a nullable integer type.
* Remove only exact duplicate rows.
* Preserve multiple inspections for the same restaurant (`camis` is **not** used for deduplication).
* Derive `is_critical` from `critical_flag`.

Additional cleaning decisions and load-validation evidence are documented in `DQ_LOG.md`.

## Column Contract

The cleaned `inspections` table contains the following columns:

| Column                  | Type         | Notes                                     |
| ----------------------- | ------------ | ----------------------------------------- |
| `camis`                 | text         | Establishment id (not unique across rows) |
| `restaurant_name`       | text         | Renamed from `dba`                        |
| `borough`               | text         | Renamed from `boro`; `"0"` → null         |
| `zipcode`               | text         |                                           |
| `cuisine`               | text         | Renamed from `cuisine_description`        |
| `inspection_date`       | datetime     | `1900-01-01` sentinel → null              |
| `action`                | text         |                                           |
| `violation_code`        | text         |                                           |
| `violation_description` | text         |                                           |
| `critical_flag`         | text         |                                           |
| `score`                 | nullable int | Missing → null; real `0` preserved        |
| `grade`                 | text         |                                           |
| `grade_date`            | datetime     |                                           |
| `record_date`           | datetime     | Drives the incremental watermark          |
| `inspection_type`       | text         |                                           |
| `latitude`              | float        | `0` → null                                |
| `longitude`             | float        | `0` → null                                |
| `is_critical`           | bool         | Derived: `critical_flag == "Critical"`    |

A separate `etl_state` table stores pipeline state: `key`, `value`, `updated_at`.

## Testing

```bash
pytest
```

* `tests/test_transform.py` — verifies the `1900-01-01` sentinel becomes null and that exact-duplicate rows are dropped.
* `tests/test_load.py` — verifies that reloading the same frame leaves the row count unchanged (idempotency).

## Technologies

* Python
* pandas
* Pydantic
* requests
* SQLAlchemy
* SQLite
* Typer (CLI)
* pytest

## Repository Structure

```text
src/
    config.py        # Config dataclass + endpoint / page size / db paths
    extract.py       # API session, paginated fetch, retry/backoff, raw landing, $where builder
    models.py        # Pydantic InspectionRecord + validate_records()
    transform.py     # standardize / coerce / clean / derive
    load.py          # engine, full + incremental load, watermark read/write, verify
    cli.py           # Typer commands (run, run --full, extract, transform/load stubs)

data/
    raw/             # bronze JSON landing (gitignored except .gitkeep)

tests/
    test_transform.py
    test_load.py

DQ_LOG.md
requirements.txt
README.md
```

## Known Limitations

* Standalone `transform` and `load` CLI commands are stubs; there is no persisted processed-data artifact between steps, so the working entry point is `run`.
* The `extract` command accepts a `--since` option, but it is not yet passed through to the extraction layer.
* On a successful load, the `run` summary still prints a "No new valid rows to load." line; this is a cosmetic output issue, not a load problem.

## Installation

```bash
pip install -r requirements.txt
```

## Notes

Large generated files such as raw API dumps, SQLite databases, virtual environments, cache directories, and IDE-specific files are intentionally excluded from version control.