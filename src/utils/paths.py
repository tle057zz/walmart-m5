"""Path helpers."""

from __future__ import annotations

from pathlib import Path

from src.config import RAW_DATA_DIR, RAW_FILES


def raw_file_path(source_key: str) -> Path:
    """Return the absolute path for a configured raw source file."""
    try:
        filename = RAW_FILES[source_key]["filename"]
    except KeyError as exc:
        raise KeyError(f"Unknown raw source key: {source_key}") from exc
    return RAW_DATA_DIR / filename


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
