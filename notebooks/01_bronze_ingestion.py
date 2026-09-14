# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Bronze ingestion (Walmart M5)
# MAGIC
# MAGIC This notebook loads the three raw M5 CSV files from the project Volume into
# MAGIC **Bronze Delta tables** with light ingestion metadata.
# MAGIC
# MAGIC | Source file | Bronze table |
# MAGIC |---|---|
# MAGIC | `calendar.csv` | `workspace.walmart_m5_bronze.bronze_calendar` |
# MAGIC | `sell_prices.csv` | `workspace.walmart_m5_bronze.bronze_sell_prices` |
# MAGIC | `sales_train_evaluation.csv` | `workspace.walmart_m5_bronze.bronze_sales` |
# MAGIC
# MAGIC Bronze rule: keep source data as-is, only add lineage metadata.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Project configuration
# MAGIC
# MAGIC Set catalog / schema / volume paths for this project only
# MAGIC (`walmart_m5_*` — separate from other projects in the same account).

# COMMAND ----------

from datetime import datetime, timezone
from uuid import uuid4

from pyspark.sql import functions as F

CATALOG = "workspace"
BRONZE_SCHEMA = "walmart_m5_bronze"
VOLUME_NAME = "raw_files"

BRONZE_FULL_SCHEMA = f"{CATALOG}.{BRONZE_SCHEMA}"
VOLUME_PATH = f"/Volumes/{CATALOG}/{BRONZE_SCHEMA}/{VOLUME_NAME}"

FILES = {
    "calendar": f"{VOLUME_PATH}/calendar.csv",
    "sell_prices": f"{VOLUME_PATH}/sell_prices.csv",
    "sales": f"{VOLUME_PATH}/sales_train_evaluation.csv",
}

TABLES = {
    "calendar": f"{BRONZE_FULL_SCHEMA}.bronze_calendar",
    "sell_prices": f"{BRONZE_FULL_SCHEMA}.bronze_sell_prices",
    "sales": f"{BRONZE_FULL_SCHEMA}.bronze_sales",
}

print("Bronze schema:", BRONZE_FULL_SCHEMA)
print("Volume path:", VOLUME_PATH)
for key, path in FILES.items():
    print(f"{key}: {path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) Confirm raw files are visible
# MAGIC
# MAGIC List files in the Volume before reading. If this fails, re-check the
# MAGIC upload path: `/Volumes/workspace/walmart_m5_bronze/raw_files/`.

# COMMAND ----------

display(dbutils.fs.ls(VOLUME_PATH))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Create ingestion batch metadata
# MAGIC
# MAGIC Every Bronze row gets:
# MAGIC - `_batch_id`
# MAGIC - `_ingestion_timestamp`
# MAGIC - `_ingestion_date`
# MAGIC - `_source_file`

# COMMAND ----------

ingestion_timestamp = datetime.now(timezone.utc)
batch_id = f"m5_{ingestion_timestamp.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
ingestion_ts_str = ingestion_timestamp.isoformat()
ingestion_date_str = ingestion_timestamp.date().isoformat()

print("batch_id:", batch_id)
print("ingestion_timestamp:", ingestion_ts_str)
print("ingestion_date:", ingestion_date_str)


def add_ingestion_metadata(df, source_file: str):
    return (
        df.withColumn("_batch_id", F.lit(batch_id))
        .withColumn("_ingestion_timestamp", F.lit(ingestion_ts_str).cast("timestamp"))
        .withColumn("_ingestion_date", F.lit(ingestion_date_str).cast("date"))
        .withColumn("_source_file", F.lit(source_file))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) Ensure Bronze schema exists
# MAGIC
# MAGIC Safe to re-run. Creates `workspace.walmart_m5_bronze` if missing.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {BRONZE_FULL_SCHEMA}")
print(f"Schema ready: {BRONZE_FULL_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) Load `bronze_calendar`
# MAGIC
# MAGIC Read `calendar.csv` and write Delta table
# MAGIC `workspace.walmart_m5_bronze.bronze_calendar`.

# COMMAND ----------

calendar_df = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .csv(FILES["calendar"])
)

calendar_bronze = add_ingestion_metadata(calendar_df, "calendar.csv")

(
    calendar_bronze.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TABLES["calendar"])
)

print("Wrote:", TABLES["calendar"])
print("Rows:", calendar_bronze.count())
display(calendar_bronze.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) Load `bronze_sell_prices`
# MAGIC
# MAGIC Read `sell_prices.csv` and write Delta table
# MAGIC `workspace.walmart_m5_bronze.bronze_sell_prices`.
# MAGIC
# MAGIC This file is large (~6.8M rows); the write may take a few minutes on Free Edition.

# COMMAND ----------

prices_df = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .csv(FILES["sell_prices"])
)

prices_bronze = add_ingestion_metadata(prices_df, "sell_prices.csv")

(
    prices_bronze.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TABLES["sell_prices"])
)

print("Wrote:", TABLES["sell_prices"])
print("Rows:", prices_bronze.count())
display(prices_bronze.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7) Load `bronze_sales`
# MAGIC
# MAGIC Read `sales_train_evaluation.csv` (wide format with `d_1`…`d_1941`) and write
# MAGIC Delta table `workspace.walmart_m5_bronze.bronze_sales`.
# MAGIC
# MAGIC Keep wide format in Bronze. Wide → long reshape happens later in Silver.

# COMMAND ----------

sales_df = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .csv(FILES["sales"])
)

sales_bronze = add_ingestion_metadata(sales_df, "sales_train_evaluation.csv")

(
    sales_bronze.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TABLES["sales"])
)

print("Wrote:", TABLES["sales"])
print("Rows:", sales_bronze.count())
print("Columns:", len(sales_bronze.columns))
display(sales_bronze.select("id", "item_id", "store_id", "state_id", "_batch_id", "_source_file").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8) Validate Bronze tables
# MAGIC
# MAGIC Check that all three tables exist and row counts look correct:
# MAGIC - calendar ≈ 1,969
# MAGIC - sales ≈ 30,490
# MAGIC - sell_prices ≈ 6,841,121

# COMMAND ----------

expected = {
    TABLES["calendar"]: 1969,
    TABLES["sales"]: 30490,
    TABLES["sell_prices"]: 6841121,
}

rows = []
for table_name, expected_count in expected.items():
    actual = spark.table(table_name).count()
    rows.append(
        (
            table_name,
            actual,
            expected_count,
            actual == expected_count,
        )
    )
    print(f"{table_name}: actual={actual:,} expected={expected_count:,} ok={actual == expected_count}")

validation_df = spark.createDataFrame(
    rows, ["table_name", "actual_rows", "expected_rows", "ok"]
)
display(validation_df)

failed = [r for r in rows if not r[3]]
if failed:
    raise ValueError(f"Bronze validation failed for: {[r[0] for r in failed]}")

print("Bronze validation passed for batch:", batch_id)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9) Quick preview with SQL
# MAGIC
# MAGIC Optional checks in SQL against the Bronze layer.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'bronze_calendar' AS table_name, COUNT(*) AS row_count
# MAGIC FROM workspace.walmart_m5_bronze.bronze_calendar
# MAGIC UNION ALL
# MAGIC SELECT 'bronze_sales', COUNT(*)
# MAGIC FROM workspace.walmart_m5_bronze.bronze_sales
# MAGIC UNION ALL
# MAGIC SELECT 'bronze_sell_prices', COUNT(*)
# MAGIC FROM workspace.walmart_m5_bronze.bronze_sell_prices;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Bronze load complete for this batch.
# MAGIC
# MAGIC **Next:**
# MAGIC 1. Confirm tables in Catalog → `workspace.walmart_m5_bronze`
# MAGIC 2. Later: wire Airflow `load_*` tasks to run this notebook / job
# MAGIC 3. Then build Silver transforms (wide → long sales, cleans, joins)
