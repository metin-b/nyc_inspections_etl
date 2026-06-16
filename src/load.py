"""Load layer (clean frame -> SQLite, idempotent + incremental)."""
from __future__ import annotations
from datetime import date
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from .config import Config

STATE_TABLE = "etl_state"
WATERMARK_KEY = "record_date_watermark"


def get_engine(cfg: Config) -> Engine:
    """SQLAlchemy engine for the SQLite file."""
    return create_engine(f"sqlite:///{cfg.db_path}")


def table_exists(engine: Engine, table: str) -> bool:
    """Return True when a table already exists in the database."""
    return inspect(engine).has_table(table)


def load_frame(df: pd.DataFrame, engine: Engine, *, table: str) -> None:
    """Replace the target table with the provided DataFrame."""
    df.to_sql(table, engine, if_exists='replace', index=False)


def _ensure_state_table(engine: Engine) -> None:
    """Create the ETL state table if it does not already exist."""
    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {STATE_TABLE} 
                (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))


def read_watermark(engine: Engine) -> date | None:
    """Read the latest loaded record_date from the ETL state table.

    Returns None on the first run.
    """
    _ensure_state_table(engine)
    with engine.connect() as conn:
        value = conn.execute(
            text(f'SELECT value FROM {STATE_TABLE} WHERE key = :key'),
            {'key': WATERMARK_KEY},
        ).scalar_one_or_none()

    if value is None:
        return None

    return pd.to_datetime(value).to_pydatetime()


def write_watermark(engine: Engine, value: date) -> None:
    """Store the latest processed inspection date."""
    _ensure_state_table(engine)
    value_text = pd.Timestamp(value).isoformat()

    with engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO {STATE_TABLE} (key, value, updated_at)
            VALUES (:key, :value, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
        """), {'key': WATERMARK_KEY, 'value': value_text})
    pass


def latest_record_date(df: pd.DataFrame) -> datetime | None:
    """Return the max record_date in a cleaned DataFrame, or None if available."""
    if df.empty or 'record_date' not in df.columns:
        return None

    record_dates = pd.to_datetime(df['record_date'], errors='coerce')
    max_value = record_dates.max()

    if pd.isna(max_value):
        return None

    return max_value.to_pydatetime()


def merge_incremental(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    """Merge existing warehouse rows with newly extracted rows.

    The source does not expose a stable row id in the return payload, so the
    safest merge is append + exact deduplication. This keeps reruns idempotent
    while avoding a full API pull every time.
    """
    if existing_df.empty:
        return new_df.drop_duplicates().reset_index(drop=True)

    if new_df.empty:
        return existing_df.drop_duplicates().reset_index(drop=True)

    merged = pd.concat([existing_df, new_df], ignore_index=True)
    return merged.drop_duplicates().reset_index(drop=True)


def load_incremental(df: pd.DataFrame, engine: Engine, *, table: str) -> int:
    """Merge new rows into the warehouse table and update the watermark

    Return the final row count in the target table.
    """
    if table_exists(engine, table):
        existing_df = pd.read_sql_table(table, engine)
    else:
        existing_df = pd.DataFrame()

    merged_df = merge_incremental(existing_df, df)
    load_frame(merged_df, engine, table=table)

    watermark = latest_record_date(merged_df)

    if watermark is not None:
        write_watermark(engine, watermark)

    return verify(engine, table)


def verify(engine: Engine, table: str) -> int:
    """Return the number of rows currently stored in the table."""
    with engine.connect() as conn:
        return conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()

