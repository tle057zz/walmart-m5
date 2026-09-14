"""Project configuration for raw-file ingestion."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INGESTION_MANIFEST_DIR = PROJECT_ROOT / "data" / "ingestion" / "manifests"

# Expected M5 source files and light-weight contract checks.
RAW_FILES = {
    "calendar": {
        "filename": "calendar.csv",
        "bronze_table": "bronze_calendar",
        "required_columns": [
            "date",
            "wm_yr_wk",
            "weekday",
            "wday",
            "month",
            "year",
            "d",
            "event_name_1",
            "event_type_1",
            "event_name_2",
            "event_type_2",
            "snap_CA",
            "snap_TX",
            "snap_WI",
        ],
        "expected_column_count": 14,
        "expected_row_count": 1969,
        "min_size_bytes": 50_000,
    },
    "sales": {
        "filename": "sales_train_evaluation.csv",
        "bronze_table": "bronze_sales",
        "required_columns": [
            "id",
            "item_id",
            "dept_id",
            "cat_id",
            "store_id",
            "state_id",
        ],
        "expected_day_columns": 1941,
        "day_column_start": "d_1",
        "day_column_end": "d_1941",
        "expected_row_count": 30_490,
        "min_size_bytes": 100_000_000,
    },
    "sell_prices": {
        "filename": "sell_prices.csv",
        "bronze_table": "bronze_sell_prices",
        "required_columns": [
            "store_id",
            "item_id",
            "wm_yr_wk",
            "sell_price",
        ],
        "expected_column_count": 4,
        "expected_row_count": 6_841_121,
        "min_size_bytes": 150_000_000,
    },
}
