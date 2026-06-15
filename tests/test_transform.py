"""Test YOUR logic, not the API. Use small fixed samples."""
import pandas as pd
from src.transform import coerce_types, handle_sentinels_and_nulls, dedup


def test_sentinel_date_becomes_null():
    df = pd.DataFrame({
        "camis": ["1"],
        "restaurant_name": ["Test Restaurant"],
        "borough": ["Manhattan"],
        "zipcode": ["10001"],
        "cuisine": ["Pizza"],
        "action": ["Violations were cited"],
        "violation_code": ["10F"],
        "violation_description": ["Something"],
        "critical_flag": ["Not Critical"],
        "grade": ["A"],
        "inspection_type": ["Cycle Inspection"],
        "inspection_date": ["1900-01-01"],
        "grade_date": ["2024-01-01"],
        "record_date": ["2024-01-02"],
        "score": ["10"],
        "latitude": ["40.0"],
        "longitude": ["-73.0"],
    })

    df = coerce_types(df)
    df = handle_sentinels_and_nulls(df)

    assert pd.isna(df.loc[0, "inspection_date"])


def test_dedup_removes_exact_duplicate_rows():
    df = pd.DataFrame({
        "camis": ["1", "1", "2"],
        "restaurant_name": ["A", "A", "B"],
        "score": [10, 10, 20],
    })

    result = dedup(df)

    assert len(result) == 2
