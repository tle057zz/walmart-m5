"""CLI entrypoint for Stage 1 raw ingestion checks + metadata generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python src/ingestion/run_ingestion.py` from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import INGESTION_MANIFEST_DIR
from src.ingestion.metadata import build_ingestion_manifest
from src.utils.logging_utils import get_logger
from src.utils.paths import ensure_dir
from src.validation.raw_files import validate_all_raw_files

logger = get_logger("walmart_m5.ingestion")


def run_ingestion(write_manifest: bool = True) -> dict:
    """
    Detect and validate raw M5 files, then emit ingestion metadata.

    This is the local Python gate before Airflow triggers Bronze loads.
    """
    logger.info("Starting raw source detection and validation")
    validations = validate_all_raw_files()

    for result in validations:
        status = "OK" if result.ok else "FAIL"
        logger.info(
            "%s | %s | rows=%s | size_bytes=%s | %s",
            status,
            result.filename,
            result.row_count,
            result.size_bytes,
            result.bronze_table,
        )
        for error in result.errors:
            logger.error("%s: %s", result.filename, error)

    manifest = build_ingestion_manifest(validations)
    logger.info(
        "Batch %s status=%s files=%s",
        manifest["batch_id"],
        manifest["status"],
        len(manifest["files"]),
    )

    if write_manifest:
        ensure_dir(INGESTION_MANIFEST_DIR)
        out_path = INGESTION_MANIFEST_DIR / f"{manifest['batch_id']}.json"
        out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        latest_path = INGESTION_MANIFEST_DIR / "latest.json"
        latest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("Wrote manifest: %s", out_path)

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Walmart M5 raw files and generate ingestion metadata."
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Validate only; do not write a manifest JSON file.",
    )
    args = parser.parse_args(argv)

    manifest = run_ingestion(write_manifest=not args.no_write)
    return 0 if manifest["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
