"""Validate Walmart M5 raw CSV files before Bronze ingestion."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.config import RAW_FILES
from src.utils.paths import raw_file_path


@dataclass
class ValidationResult:
    source_key: str
    filename: str
    path: str
    exists: bool
    size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    columns: list[str] = field(default_factory=list)
    day_column_count: int | None = None
    bronze_table: str | None = None
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and all(self.checks.values())

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ok"] = self.ok
        return payload


def _count_data_rows(path: Path) -> int:
    """Count CSV data rows (excludes header) without loading the full file."""
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def _read_header(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
    if not header:
        raise ValueError(f"{path.name} has no header row")
    return header


def validate_raw_file(source_key: str) -> ValidationResult:
    """Validate a single configured raw source file."""
    spec = RAW_FILES[source_key]
    path = raw_file_path(source_key)
    result = ValidationResult(
        source_key=source_key,
        filename=spec["filename"],
        path=str(path),
        exists=path.exists(),
        bronze_table=spec["bronze_table"],
    )

    if not result.exists:
        result.errors.append(f"Missing file: {path}")
        result.checks["file_exists"] = False
        return result

    result.checks["file_exists"] = True
    result.size_bytes = path.stat().st_size
    result.checks["min_size"] = result.size_bytes >= spec["min_size_bytes"]
    if not result.checks["min_size"]:
        result.errors.append(
            f"File too small: {result.size_bytes} bytes "
            f"(min {spec['min_size_bytes']})"
        )

    try:
        header = _read_header(path)
    except ValueError as exc:
        result.errors.append(str(exc))
        result.checks["readable_header"] = False
        return result

    result.checks["readable_header"] = True
    result.columns = header
    result.column_count = len(header)

    missing = [col for col in spec["required_columns"] if col not in header]
    result.checks["required_columns"] = not missing
    if missing:
        result.errors.append(f"Missing required columns: {missing}")

    if "expected_column_count" in spec:
        result.checks["column_count"] = result.column_count == spec["expected_column_count"]
        if not result.checks["column_count"]:
            result.errors.append(
                f"Expected {spec['expected_column_count']} columns, "
                f"found {result.column_count}"
            )

    if source_key == "sales":
        day_cols = [col for col in header if col.startswith("d_")]
        result.day_column_count = len(day_cols)
        expected_days = spec["expected_day_columns"]
        result.checks["day_columns"] = (
            len(day_cols) == expected_days
            and day_cols
            and day_cols[0] == spec["day_column_start"]
            and day_cols[-1] == spec["day_column_end"]
        )
        if not result.checks["day_columns"]:
            result.errors.append(
                f"Expected day columns {spec['day_column_start']}.."
                f"{spec['day_column_end']} ({expected_days} total), "
                f"found {len(day_cols)}"
            )

    result.row_count = _count_data_rows(path)
    result.checks["row_count"] = result.row_count == spec["expected_row_count"]
    if not result.checks["row_count"]:
        result.errors.append(
            f"Expected {spec['expected_row_count']} rows, found {result.row_count}"
        )

    return result


def validate_all_raw_files() -> list[ValidationResult]:
    return [validate_raw_file(source_key) for source_key in RAW_FILES]
