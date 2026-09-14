"""Airflow-callable tasks for the M5 ingestion gate."""

from __future__ import annotations

import json
from pathlib import Path

from src.config import INGESTION_MANIFEST_DIR, RAW_DATA_DIR, RAW_FILES
from src.ingestion.metadata import build_ingestion_manifest
from src.utils.logging_utils import get_logger
from src.utils.paths import ensure_dir, raw_file_path
from src.validation.raw_files import validate_all_raw_files, validate_raw_file

logger = get_logger("walmart_m5.airflow_tasks")

BRONZE_STAGING_DIR = INGESTION_MANIFEST_DIR.parent / "bronze_staging"


def check_source_files() -> list[str]:
    """Fail fast if any required raw CSV is missing."""
    missing = []
    found = []
    for source_key, spec in RAW_FILES.items():
        path = raw_file_path(source_key)
        if path.exists():
            found.append(spec["filename"])
            logger.info("Found source file: %s", path)
        else:
            missing.append(str(path))
            logger.error("Missing source file: %s", path)

    if missing:
        raise FileNotFoundError(
            "Missing required raw files under "
            f"{RAW_DATA_DIR}: {missing}"
        )
    return found


def validate_raw_files() -> dict:
    """Run full raw validation and write the ingestion manifest."""
    validations = validate_all_raw_files()
    for result in validations:
        status = "OK" if result.ok else "FAIL"
        logger.info(
            "%s | %s | rows=%s | size_bytes=%s",
            status,
            result.filename,
            result.row_count,
            result.size_bytes,
        )
        for error in result.errors:
            logger.error("%s: %s", result.filename, error)

    manifest = build_ingestion_manifest(validations)
    ensure_dir(INGESTION_MANIFEST_DIR)
    out_path = INGESTION_MANIFEST_DIR / f"{manifest['batch_id']}.json"
    latest_path = INGESTION_MANIFEST_DIR / "latest.json"
    payload = json.dumps(manifest, indent=2)
    out_path.write_text(payload, encoding="utf-8")
    latest_path.write_text(payload, encoding="utf-8")
    logger.info("Wrote manifest: %s", out_path)

    if manifest["status"] != "ready":
        raise ValueError(
            f"Raw validation failed for batch {manifest['batch_id']}"
        )
    return manifest


def _load_latest_manifest() -> dict:
    latest = INGESTION_MANIFEST_DIR / "latest.json"
    if not latest.exists():
        raise FileNotFoundError(
            f"Missing ingestion manifest: {latest}. "
            "Run validate_raw_files first."
        )
    return json.loads(latest.read_text(encoding="utf-8"))


def stage_bronze_load(source_key: str) -> dict:
    """
    Stage a Bronze load marker for one source.

    Databricks Delta writes come later; this task proves the parallel
    load branch and records lineage from the latest ready manifest.
    """
    if source_key not in RAW_FILES:
        raise KeyError(f"Unknown source_key: {source_key}")

    # Re-check the individual file before staging.
    result = validate_raw_file(source_key)
    if not result.ok:
        raise ValueError(
            f"Cannot stage {source_key}; validation errors: {result.errors}"
        )

    manifest = _load_latest_manifest()
    file_meta = next(
        (item for item in manifest["files"] if item["source_key"] == source_key),
        None,
    )
    if file_meta is None:
        raise KeyError(f"{source_key} not found in latest manifest")

    ensure_dir(BRONZE_STAGING_DIR)
    bronze_table = RAW_FILES[source_key]["bronze_table"]
    out_path = BRONZE_STAGING_DIR / f"{bronze_table}__{manifest['batch_id']}.json"
    staging_record = {
        "status": "staged",
        "note": "Placeholder until Databricks Bronze load is wired",
        "bronze_table": bronze_table,
        "source_key": source_key,
        "batch_id": manifest["batch_id"],
        "source_file": file_meta["_source_file"],
        "row_count": file_meta["row_count"],
        "ingestion_timestamp": file_meta["_ingestion_timestamp"],
    }
    out_path.write_text(json.dumps(staging_record, indent=2), encoding="utf-8")
    logger.info("Staged Bronze marker: %s", out_path)
    return staging_record


def validate_bronze_staging() -> dict:
    """Confirm all three Bronze staging markers exist for the latest batch."""
    manifest = _load_latest_manifest()
    batch_id = manifest["batch_id"]
    missing = []
    found = []
    for source_key, spec in RAW_FILES.items():
        path = BRONZE_STAGING_DIR / f"{spec['bronze_table']}__{batch_id}.json"
        if path.exists():
            found.append(str(path))
        else:
            missing.append(str(path))

    if missing:
        raise FileNotFoundError(f"Missing Bronze staging markers: {missing}")

    summary = {
        "batch_id": batch_id,
        "status": "bronze_staging_ok",
        "markers": found,
    }
    logger.info("Bronze staging validation passed for batch %s", batch_id)
    return summary


def record_databricks_run(job_id: str) -> dict:
    """
    Record that the Databricks Medallion job was triggered successfully.

    Airflow's DatabricksRunNowOperator already waited for job success before
    this task runs; this writes a local audit marker tied to the latest batch.
    """
    if not job_id or job_id.startswith("0000"):
        raise ValueError(
            "WALMART_M5_DATABRICKS_JOB_ID is not configured. "
            "Set it in airflow/.env to your Databricks job id."
        )

    manifest = _load_latest_manifest()
    ensure_dir(INGESTION_MANIFEST_DIR)
    record = {
        "status": "databricks_medallion_success",
        "batch_id": manifest["batch_id"],
        "databricks_job_id": str(job_id),
        "layers": ["bronze", "silver", "gold"],
        "notebooks": [
            "01_bronze_ingestion",
            "02_silver_sales",
            "03_silver_products",
            "04_silver_calendar",
            "05_gold_dimensions",
            "06_gold_facts",
            "07_gold_aggregations",
        ],
    }
    out_path = (
        INGESTION_MANIFEST_DIR
        / f"databricks_run__{manifest['batch_id']}.json"
    )
    latest = INGESTION_MANIFEST_DIR / "databricks_run_latest.json"
    payload = json.dumps(record, indent=2)
    out_path.write_text(payload, encoding="utf-8")
    latest.write_text(payload, encoding="utf-8")
    logger.info("Recorded Databricks success marker: %s", out_path)
    return record
