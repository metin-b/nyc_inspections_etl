# NYC Restaurant Inspections ETL

A Python ETL project that extracts New York City restaurant inspection data from the NYC Open Data (Socrata) API, validates records with Pydantic, cleans and standardizes the data with pandas, and loads the results into a SQLite data warehouse.

## Project Goals

* Extract restaurant inspection records from the public API.
* Preserve the original API response as a raw ("bronze") JSON dataset.
* Validate incoming records using Pydantic models.
* Apply documented data-quality rules and transformations.
* Produce a clean, consistent dataset ready for analysis and reporting.
* Load the cleaned data into SQLite in an idempotent manner.

## Data Source

**NYC Open Data – Restaurant Inspection Results**

API endpoint:

```text
https://data.cityofnewyork.us/resource/43nn-pn8j.json
```

## Architecture

```text
NYC Open Data API
        │
        ▼
Extract
(download + pagination)
        │
        ▼
Raw JSON (data/raw)
        │
        ▼
Validate (Pydantic)
        │
        ▼
Transform (pandas)
        │
        ▼
SQLite Warehouse
```

## Current Features

* API extraction with pagination
* Raw JSON landing for reproducible processing
* Pydantic schema validation
* Column standardization
* Text normalization
* Sentinel value handling
* Type coercion
* Exact duplicate removal
* Derived `is_critical` field

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

Additional cleaning decisions are documented in `DQ_LOG.md`.

## Technologies

* Python
* pandas
* Pydantic
* requests
* SQLAlchemy
* SQLite

## Repository Structure

```text
src/
    config.py
    extract.py
    models.py
    transform.py
    load.py
    cli.py

data/
    raw/

tests/

DQ_LOG.md
requirements.txt
README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Notes

Large generated files such as raw API dumps, SQLite databases, virtual environments, cache directories, and IDE-specific files are intentionally excluded from version control.
