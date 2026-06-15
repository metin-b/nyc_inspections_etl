"""Idempotency test against an in-memory SQLite engine."""
import pandas as pd
from sqlalchemy import create_engine
from src.load import load_frame, verify


def test_load_is_idempotent():
    engine = create_engine("sqlite:///:memory:")

    df = pd.DataFrame({
        'camis': ['1', '2'],
        'restaurant_name': ['A', 'B'],
        'score': [10, 20]
    })

    load_frame(df, engine, table='inspections')
    first_count = verify(engine, 'inspections')

    load_frame(df, engine, table='inspections')
    second_count = verify(engine, 'inspections')

    assert first_count == 2
    assert second_count == 2

test_load_is_idempotent()