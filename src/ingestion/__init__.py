"""Python ingestion package for Walmart M5 raw sources."""

from src.ingestion.metadata import build_ingestion_manifest
from src.ingestion.run_ingestion import run_ingestion

__all__ = ["build_ingestion_manifest", "run_ingestion"]
