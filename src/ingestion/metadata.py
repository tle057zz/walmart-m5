"""Ingestion metadata helpers for Bronze loads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.validation.raw_files import ValidationResult


def new_batch_id(prefix: str = "m5") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{stamp}_{uuid4().hex[:8]}"


def build_file_metadata(
    validation: ValidationResult,
    *,
    batch_id: str,
    ingestion_timestamp: str,
) -> dict[str, Any]:
    """Build per-file metadata fields intended for Bronze enrichment."""
    return {
        "_batch_id": batch_id,
        "_ingestion_timestamp": ingestion_timestamp,
        "_ingestion_date": ingestion_timestamp[:10],
        "_source_file": validation.filename,
        "source_key": validation.source_key,
        "bronze_table": validation.bronze_table,
        "path": validation.path,
        "size_bytes": validation.size_bytes,
        "row_count": validation.row_count,
        "column_count": validation.column_count,
        "day_column_count": validation.day_column_count,
        "validation_ok": validation.ok,
        "validation_errors": validation.errors,
        "checks": validation.checks,
    }


def build_ingestion_manifest(
    validations: list[ValidationResult],
    *,
    batch_id: str | None = None,
) -> dict[str, Any]:
    """Assemble a batch-level ingestion manifest from validation results."""
    batch_id = batch_id or new_batch_id()
    ingestion_timestamp = datetime.now(timezone.utc).isoformat()
    files = [
        build_file_metadata(
            result,
            batch_id=batch_id,
            ingestion_timestamp=ingestion_timestamp,
        )
        for result in validations
    ]
    return {
        "batch_id": batch_id,
        "ingestion_timestamp": ingestion_timestamp,
        "status": "ready" if all(item["validation_ok"] for item in files) else "failed",
        "files": files,
        "bronze_targets": [
            {
                "source_key": item["source_key"],
                "bronze_table": item["bronze_table"],
                "source_file": item["_source_file"],
            }
            for item in files
        ],
    }
