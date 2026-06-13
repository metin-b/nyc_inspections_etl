"""Validate layer (raw dicts -> trusted records). Schema-on-read with Pydantic v2."""
from __future__ import annotations
from pydantic import BaseModel, ValidationError


class InspectionRecord(BaseModel):
    """Validated representation of a restaurant inspection record."""
    camis: str
    dba: str | None = None
    boro: str | None = None
    zipcode: str | None = None
    cuisine_description: str | None = None
    inspection_date: str | None = None
    action: str | None = None
    violation_code: str | None = None
    violation_description: str | None = None
    critical_flag: str | None = None
    score: int | None = None
    grade: str | None = None
    grade_date: str | None = None
    record_date: str | None = None
    inspection_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None


def validate_records(raw: list[dict]) -> tuple[list[InspectionRecord], list[dict]]:
    """Validate raw records and separate successful and failed parses."""

    good_records = []
    bad_rows = []

    for row in raw:
        try:
            record = InspectionRecord(**row)
            good_records.append(record)
        except ValidationError as e:
            bad_rows.append({
                'row': row,
                'errors': e.errors()
            })

    return good_records, bad_rows