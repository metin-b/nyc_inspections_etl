# Data Quality Log

## Transform decisions

- Renamed `dba` to `restaurant_name`, `boro` to `borough`, and `cuisine_description` to `cuisine` to match the final column contract.
- Stripped whitespace from text columns and converted empty strings to null values.
- Converted `inspection_date`, `grade_date`, and `record_date` to pandas datetime values.
- Converted `score` to nullable integer so missing scores stay null while real `0` scores remain valid.
- Converted `latitude` and `longitude` to floats.
- Converted fake `inspection_date` value `1900-01-01` to null because it represents an uninspected/new establishment.
- Converted `borough == "0"` to null because it is a junk placeholder.
- Converted `latitude == 0` and `longitude == 0` to null because zero coordinates are placeholders.
- Dropped exact duplicate rows only; did not deduplicate on `camis` because restaurants can have many inspections.
- Derived `is_critical` as `True` only when `critical_flag == "Critical"`.
- Did not add an outlier column in the final table to keep the DataFrame aligned with the Column Contract.

## Full refresh load validation — 2026-06-15

### Pipeline run

Ran the end-to-end full refresh pipeline with:

```powershell
.\.venv\Scripts\python.exe -m src.cli run
```

### Output

```text
Raw file: data\raw\nyc_inspections_raw_20260615_175258.json
Loaded rows: 297407
DataFrame rows: 297407
Bad rows: 0
```

### Validation result

* Pydantic validation completed with `0` rejected rows.
* Date fields remain strings during validation.
* Date conversion happens in the transform layer using pandas.
* This keeps validation focused on record shape and basic field compatibility instead of rejecting rows for API datetime formatting.

### Load result

* Cleaned DataFrame contained `297407` rows.
* SQLite `inspections` table contained `297407` rows after load.
* verify()` confirmed that the loaded row count matched the cleaned DataFrame row count.
* Current load strategy is full refresh.
* load_frame()` uses `if_exists="replace"`, so rerunning the load replaces the table instead of appending duplicate rows.

### Current limitation

Standalone `transform` and `load` CLI commands are not fully implemented yet because no saved processed-data artifact exists between steps. The working command is currently `run`, which executes extract, validate, transform, load, and verify in one process.

## Incremental load validation — 2026-06-16

### Pipeline runs

Ran a full refresh followed by three back-to-back incremental reruns to confirm
idempotency:

```powershell
.\.venv\Scripts\python.exe -m src.cli run --full   # full refresh
.\.venv\Scripts\python.exe -m src.cli run           # incremental
.\.venv\Scripts\python.exe -m src.cli run           # incremental rerun
.\.venv\Scripts\python.exe -m src.cli run           # incremental rerun
```

### Full refresh result

* Raw file: `data/raw/nyc_inspections_raw_20260616_210002.json` (full dataset).
* `inspections` table contained `297579` rows after load (up from `297407` on 2026-06-15; NYC published additional records for the same publish batch).
* Watermark written to `etl_state` as `record_date_watermark = 2026-06-15T06:00:42` (the max `record_date` in the data), `updated_at = 2026-06-16 21:00:16`.

### Incremental rerun result

* The three incremental reruns each requested `record_date > '2026-06-15T06:00:42'`.
* Each returned an empty page; the landed raw files are empty arrays:
  * `nyc_inspections_raw_20260616_210308.json` → `[]`
  * `nyc_inspections_raw_20260616_210643.json` → `[]`
  * `nyc_inspections_raw_20260616_210811.json` → `[]`
* Because no good rows were produced, the load step short-circuited: the `inspections` table stayed at `297579` rows and the watermark was left unchanged.
* This confirms the incremental + idempotency design: reruns with no new source data neither duplicate rows nor advance the watermark.

### Warehouse snapshot (post-run)

Profiled directly from `warehouse.db`:

| Metric                     | Value     |
| -------------------------- | --------- |
| Total rows                 | 297,579   |
| Distinct `camis`           | 31,325    |
| Null `borough`             | 361       |
| Null `inspection_date`     | 3,499     |
| Null `score`               | 17,191    |
| `is_critical = True`       | 156,344   |
| Max `record_date`          | 2026-06-15 06:00:42 |

* Null `inspection_date` includes the `1900-01-01` sentinels mapped to null in transform.
* Null `score` reflects records with no score in the source, preserved as null (nullable Int64) rather than coerced to `0`.
* `camis` is intentionally non-unique: 31,325 establishments account for 297,579 inspection/violation rows, as expected.