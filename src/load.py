"""Load layer (clean frame -> SQLite, idempotent + incremental)."""
from __future__ import annotations
from datetime import date
import pandas as pd
from sqlalchemy import Engine, create_engine
from .config import Config


def get_engine(cfg: Config) -> Engine:
    """SQLAlchemy engine for the SQLite file."""
    return create_engine(f"sqlite:///{cfg.db_path}")


def load_frame(df: pd.DataFrame, engine: Engine, *, table: str) -> None:
    """Replace the target table with the provided DataFrame."""
    df.to_sql(table, engine, if_exists='replace', index=False)


def read_watermark(engine: Engine) -> date | None:
    """Read the last loaded inspection_date from a tiny state table (None on first run)."""
    pass


def write_watermark(engine: Engine, value: date) -> None:
    """Store the latest processed inspection date."""
    pass


def verify(engine: Engine, table: str) -> int:
    """Return the number of rows currently stored in the table."""
    with engine.connect() as conn:
        return conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()

