"""Typer CLI. Each layer is runnable on its own; `run` does the whole pipeline."""
from __future__ import annotations
import typer
from .config import Config
from .extract import make_session, extract_all, land_raw
from .models import validate_records
from .transform import to_frame, clean
from .load import get_engine, load_frame, verify

app = typer.Typer(help="NYC restaurant-inspection ETL")


@app.command()
def extract(since: str = typer.Option(None, help="ISO date; only inspections on/after this")):
    """Pull from the API and land raw JSON to data/raw/."""
    cfg = Config.from_env()

    session = make_session(cfg)
    raw_records = list(extract_all(session, cfg))
    raw_path = land_raw(raw_records, cfg)

    typer.echo(f'Extracted rows: {len(raw_records)}')
    typer.echo(f'Raw File: {raw_path}')

@app.command()
def transform():
    """Validate + clean the latest raw pull into a clean frame."""
    typer.echo("Standalone transform command is not implemented yet. Use `run` for now.")

@app.command()
def load():
    """Load the clean frame into SQLite."""
    typer.echo("Standalone load command is not implemented yet. Use `run` for now.")


@app.command()
def run(
    since: str = typer.Option(None, help="ISO date for an incremental pull"),
    full: bool = typer.Option(False, help="Full refresh instead of incremental"),
    page_size: int = typer.Option(1000),
    log_level: str = typer.Option("INFO"),
):
    """extract -> validate -> transform -> load, end to end."""
    cfg = Config.from_env()

    session = make_session(cfg)
    raw_records = list(extract_all(session, cfg))

    raw_path = land_raw(raw_records, cfg)

    good_rows, bad_rows = validate_records(raw_records)

    df = to_frame(good_rows)
    df = clean(df)

    engine = get_engine(cfg)
    load_frame(df, engine, table='inspections')

    row_count = verify(engine, 'inspections')

    typer.echo(f'Raw file: {raw_path}')
    typer.echo(f'Loaded rows: {row_count}')
    typer.echo(f'DataFrame rows: {len(df)}')
    typer.echo(f'Bad rows: {len(bad_rows)}')


if __name__ == "__main__":
    app()
