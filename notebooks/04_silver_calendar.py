# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Silver calendar (Walmart M5)
# MAGIC
# MAGIC Clean and standardize `bronze_calendar` into `silver_calendar`
# MAGIC for date dimension / event / SNAP enrichment in Gold.
# MAGIC
# MAGIC | From | To |
# MAGIC |---|---|
# MAGIC | `workspace.walmart_m5_bronze.bronze_calendar` | `workspace.walmart_m5_silver.silver_calendar` |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Configuration

# COMMAND ----------

from pyspark.sql import functions as F

CATALOG = "workspace"
BRONZE_SCHEMA = f"{CATALOG}.walmart_m5_bronze"
SILVER_SCHEMA = f"{CATALOG}.walmart_m5_silver"

BRONZE_CALENDAR = f"{BRONZE_SCHEMA}.bronze_calendar"
SILVER_CALENDAR = f"{SILVER_SCHEMA}.silver_calendar"

print("Source:", BRONZE_CALENDAR)
print("Target:", SILVER_CALENDAR)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) Ensure Silver schema exists

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA}")
print("Schema ready:", SILVER_SCHEMA)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Read and profile Bronze calendar

# COMMAND ----------

calendar_bronze = spark.table(BRONZE_CALENDAR)
print("Bronze calendar rows:", calendar_bronze.count())
calendar_bronze.printSchema()
display(calendar_bronze.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) Clean types and standardize columns
# MAGIC
# MAGIC - cast `date`, week, month, year, SNAP flags
# MAGIC - keep event fields as strings (null when no event)
# MAGIC - derive helpers: `event_flag`, `snap_any_flag`

# COMMAND ----------

silver_calendar = (
    calendar_bronze.select(
        F.to_date("date").alias("date"),
        F.col("wm_yr_wk").cast("int").alias("wm_yr_wk"),
        F.col("weekday").cast("string").alias("weekday"),
        F.col("wday").cast("int").alias("wday"),
        F.col("month").cast("int").alias("month"),
        F.col("year").cast("int").alias("year"),
        F.col("d").cast("string").alias("day_id"),
        F.col("event_name_1").cast("string").alias("event_name_1"),
        F.col("event_type_1").cast("string").alias("event_type_1"),
        F.col("event_name_2").cast("string").alias("event_name_2"),
        F.col("event_type_2").cast("string").alias("event_type_2"),
        F.col("snap_CA").cast("int").alias("snap_CA"),
        F.col("snap_TX").cast("int").alias("snap_TX"),
        F.col("snap_WI").cast("int").alias("snap_WI"),
    )
    .withColumn(
        "event_flag",
        F.when(
            F.col("event_name_1").isNotNull() | F.col("event_name_2").isNotNull(),
            F.lit(1),
        ).otherwise(F.lit(0)),
    )
    .withColumn(
        "snap_any_flag",
        F.when(
            (F.col("snap_CA") == 1) | (F.col("snap_TX") == 1) | (F.col("snap_WI") == 1),
            F.lit(1),
        ).otherwise(F.lit(0)),
    )
    .dropDuplicates(["date"])
)

display(silver_calendar.limit(15))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) Data-quality checks
# MAGIC
# MAGIC - unique dates
# MAGIC - no null `date` / `day_id` / `wm_yr_wk`
# MAGIC - SNAP flags in {0, 1}
# MAGIC - continuous day coverage (optional summary)

# COMMAND ----------

checks = {
    "null_date": silver_calendar.filter(F.col("date").isNull()).count(),
    "null_day_id": silver_calendar.filter(F.col("day_id").isNull()).count(),
    "null_wm_yr_wk": silver_calendar.filter(F.col("wm_yr_wk").isNull()).count(),
    "duplicate_date": (
        silver_calendar.groupBy("date").count().filter(F.col("count") > 1).count()
    ),
    "bad_snap_flags": silver_calendar.filter(
        ~F.col("snap_CA").isin(0, 1)
        | ~F.col("snap_TX").isin(0, 1)
        | ~F.col("snap_WI").isin(0, 1)
    ).count(),
}

for name, value in checks.items():
    print(f"{name}: {value}")

failed = {k: v for k, v in checks.items() if v > 0}
if failed:
    raise ValueError(f"silver_calendar quality checks failed: {failed}")

date_stats = silver_calendar.agg(
    F.min("date").alias("min_date"),
    F.max("date").alias("max_date"),
    F.countDistinct("date").alias("distinct_dates"),
).collect()[0]

print(
    "Date range:",
    date_stats["min_date"],
    "→",
    date_stats["max_date"],
    "| distinct:",
    date_stats["distinct_dates"],
)
print("silver_calendar quality checks passed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) Write `silver_calendar`

# COMMAND ----------

(
    silver_calendar.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(SILVER_CALENDAR)
)

print("Wrote:", SILVER_CALENDAR)
print("Rows:", spark.table(SILVER_CALENDAR).count())
display(spark.table(SILVER_CALENDAR).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7) SQL preview — events & SNAP

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   year,
# MAGIC   COUNT(*) AS days,
# MAGIC   SUM(event_flag) AS event_days,
# MAGIC   SUM(snap_CA) AS snap_ca_days,
# MAGIC   SUM(snap_TX) AS snap_tx_days,
# MAGIC   SUM(snap_WI) AS snap_wi_days
# MAGIC FROM workspace.walmart_m5_silver.silver_calendar
# MAGIC GROUP BY year
# MAGIC ORDER BY year;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done — Silver layer complete
# MAGIC
# MAGIC Silver tables now available:
# MAGIC - `silver_sales`
# MAGIC - `silver_products`
# MAGIC - `silver_stores`
# MAGIC - `silver_sell_prices`
# MAGIC - `silver_calendar`
# MAGIC
# MAGIC **Next notebooks (Gold):**
# MAGIC 1. `05_gold_dimensions` → `dim_date`, `dim_product`, `dim_store`
# MAGIC 2. `06_gold_facts` → `fact_daily_sales`, `fact_product_prices`
# MAGIC 3. `07_gold_aggregations` → store / category / demand aggregates
