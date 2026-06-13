"""Data transformation and cleaning utilities."""
import pandas as pd
from .models import InspectionRecord
import numpy as np


def to_frame(records: list[InspectionRecord]) -> pd.DataFrame:
    """Convert validated records into a pandas DataFrame."""
    return pd.DataFrame([r.model_dump() for r in records])


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to the project's standard schema."""
    return df.rename(columns={
        'dba': 'restaurant_name',
        'boro': 'borough',
        'cuisine_description': 'cuisine'})

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert columns to their expected data types."""
    df["inspection_date"] = pd.to_datetime(df["inspection_date"], errors="coerce")
    df["grade_date"] = pd.to_datetime(df["grade_date"], errors="coerce")
    df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce")
    df['score'] = pd.to_numeric(df['score'], errors='coerce').astype('Int64')
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    return df


def dedup(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate records."""
    return df.drop_duplicates()

def handle_sentinels_and_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize placeholder values and missing data."""
    text_cols = [
        "camis", "restaurant_name", "borough", "zipcode", "cuisine",
        "action", "violation_code", "violation_description",
        "critical_flag", "grade", "inspection_type"
    ]
    for i in text_cols:
        df[i] = df[i].str.strip()
        df[i] = df[i].replace('', pd.NA)

    df['borough'] = df['borough'].replace('0', pd.NA)
    df['longitude'] = df['longitude'].replace(0.0, np.nan)
    df['latitude'] = df['latitude'].replace(0.0, np.nan)
    df["inspection_date"] = df["inspection_date"].mask(df["inspection_date"] == pd.Timestamp("1900-01-01"), None)
    return df


def derive_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived columns used downstream."""
    df["is_critical"] = df["critical_flag"] == "Critical"
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Run the complete cleaning pipeline."""
    df = standardize_columns(df)
    df = coerce_types(df)
    df = handle_sentinels_and_nulls(df)
    df = dedup(df)
    df = derive_columns(df)
    return df

