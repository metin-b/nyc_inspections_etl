"""Typer CLI. Each layer is runnable on its own; `run` does the whole pipeline."""
from __future__ import annotations
import typer
from .config import Config
from .models import validate_records
from .transform import to_frame, clean
from .extract import make_session, extract_all, land_raw, build_where_clause
from .load import (
    get_engine,
    load_incremental,
    load_frame,
    verify,
    read_watermark,
    latest_record_date,
    write_watermark,
    table_exists
)

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
    full: bool = typer.Option(False, help='Full refresh instead of incremental'),
):
    """extract -> validate -> transform -> load, end to end."""
    cfg = Config.from_env()
    engine = get_engine(cfg)

    if full:
        where = None
        typer.echo('Running full refresh.')
    else:
        watermark = read_watermark(engine)
        where = build_where_clause(watermark)

        if watermark is None:
            typer.echo('No watermark found. Running initial full extract.')
        else:
            typer.echo(f'Running incremental extract after: {watermark.isoformat()}')


    session = make_session(cfg)
    raw_records = list(extract_all(session, cfg, where=where))

    raw_path = land_raw(raw_records, cfg)

    good_rows, bad_rows = validate_records(raw_records)

    if not good_rows:
        if table_exists(engine, "inspections"):
            row_count = verify(engine, "inspections")
        else:
            row_count = 0

        typer.echo(f"Raw file: {raw_path}")
        typer.echo(f"Fetched rows: {len(raw_records)}")
        typer.echo(f"Accepted rows: {len(good_rows)}")
        typer.echo(f"Bad rows: {len(bad_rows)}")
        typer.echo("No new valid rows to load.")
        typer.echo(f"Loaded rows: {row_count}")
        return

    df = to_frame(good_rows)
    df = clean(df)

    if full:
        load_frame(df, engine, table="inspections")

        watermark = latest_record_date(df)
        if watermark is not None:
            write_watermark(engine, watermark)

        row_count = verify(engine, "inspections")
    else:
        row_count = load_incremental(df, engine, table="inspections")

    typer.echo(f"Raw file: {raw_path}")
    typer.echo(f"Fetched rows: {len(raw_records)}")
    typer.echo(f"Accepted rows: {len(good_rows)}")
    typer.echo(f"Bad rows: {len(bad_rows)}")
    typer.echo("No new valid rows to load.")
    typer.echo(f"Loaded rows: {row_count}")


if __name__ == "__main__":
    app()
