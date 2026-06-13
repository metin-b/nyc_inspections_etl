# Data Quality Log

## Transform decisions

- Renamed `dba` to `restaurant_name`, `boro` to `borough`, and `cuisine_description` to `cuisine` to match the final column contract.
- Stripped whitespace from text columns and converted empty strings to null values.
- Converted `inspection_date` and `grade_date` to dates; converted `record_date` to datetime.
- Converted `score` to nullable integer so missing scores stay null while real `0` scores remain valid.
- Converted `latitude` and `longitude` to floats.
- Converted fake `inspection_date` value `1900-01-01` to null because it represents an uninspected/new establishment.
- Converted `borough == "0"` to null because it is a junk placeholder.
- Converted `latitude == 0` and `longitude == 0` to null because zero coordinates are placeholders.
- Dropped exact duplicate rows only; did not deduplicate on `camis` because restaurants can have many inspections.
- Derived `is_critical` as `True` only when `critical_flag == "Critical"`.
- Did not add an outlier column in the final table to keep the DataFrame aligned with the Column Contract.