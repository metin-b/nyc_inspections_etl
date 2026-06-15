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
