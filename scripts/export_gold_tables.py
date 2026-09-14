#!/usr/bin/env python3
"""Export workspace.walmart_m5_gold tables from Databricks SQL to local files."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "gold_export"
ENV_CANDIDATES = (
    PROJECT_ROOT / "airflow" / ".env",
    PROJECT_ROOT / ".env",
)

GOLD_TABLES = [
    "agg_daily_category_sales",
    "agg_daily_store_sales",
    "agg_demand_trends",
    "agg_event_sales",
    "agg_price_analysis",
    "agg_product_performance",
    "agg_store_category_sales",
    "dim_date",
    "dim_product",
    "dim_store",
    "fact_daily_sales",
    "fact_product_prices",
]


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def hostname_from_host(host: str) -> str:
    host = host.strip()
    if "://" not in host:
        return host.split("/")[0]
    return urlparse(host).hostname or host


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Databricks gold tables to local parquet/csv files."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--format",
        choices=("parquet", "csv"),
        default="parquet",
        help="File format (default: parquet)",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=GOLD_TABLES,
        help="Tables to export (default: all gold tables)",
    )
    parser.add_argument(
        "--catalog",
        default=os.environ.get("DATABRICKS_CATALOG", "workspace"),
        help="Unity Catalog name (default: workspace)",
    )
    parser.add_argument(
        "--schema",
        default=os.environ.get("DATABRICKS_GOLD_SCHEMA", "walmart_m5_gold"),
        help="Schema name (default: walmart_m5_gold)",
    )
    return parser.parse_args()


def main() -> int:
    for env_path in ENV_CANDIDATES:
        load_dotenv(env_path)

    args = parse_args()

    try:
        import certifi
        import pandas  # noqa: F401 — required for Arrow → DataFrame / parquet write
        from databricks import sql
    except ImportError as exc:
        print(
            f"Missing dependency ({exc}). Install with:\n"
            "  .venv/bin/pip install 'databricks-sql-connector[pyarrow]' pandas pyarrow certifi",
            file=sys.stderr,
        )
        return 1

    host = os.environ.get("DATABRICKS_HOST", "").strip()
    token = os.environ.get("DATABRICKS_TOKEN", "").strip()
    http_path = os.environ.get("DATABRICKS_HTTP_PATH", "").strip()

    if not host or not token:
        print(
            "Set DATABRICKS_HOST and DATABRICKS_TOKEN (e.g. in airflow/.env).",
            file=sys.stderr,
        )
        return 1
    if not http_path:
        print(
            "Set DATABRICKS_HTTP_PATH in airflow/.env.\n"
            "Find it in Databricks → SQL Warehouses → Serverless Starter Warehouse "
            "→ Connection details → HTTP Path\n"
            "Example: /sql/1.0/warehouses/abc123def456",
            file=sys.stderr,
        )
        return 1

    server_hostname = hostname_from_host(host)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {server_hostname} …")
    print(f"Exporting {len(args.tables)} table(s) → {args.out_dir}")

    # Use certifi CA bundle so corporate / macOS Python SSL chains verify.
    connect_kwargs = {
        "server_hostname": server_hostname,
        "http_path": http_path,
        "access_token": token,
        "_tls_trusted_ca_file": certifi.where(),
    }

    with sql.connect(**connect_kwargs) as conn:
        for table in args.tables:
            fq_name = f"{args.catalog}.{args.schema}.{table}"
            print(f"  reading {fq_name} …", flush=True)
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {fq_name}")
                arrow_table = cursor.fetchall_arrow()
            df = arrow_table.to_pandas()
            out_path = args.out_dir / f"{table}.{args.format}"
            if args.format == "parquet":
                df.to_parquet(out_path, index=False)
            else:
                df.to_csv(out_path, index=False)
            print(f"  wrote {out_path.name}  rows={len(df):,}  cols={len(df.columns)}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
