# Databricks notebook source
# MAGIC %md
# MAGIC # 06 — Gold facts (Walmart M5)
# MAGIC
# MAGIC Build fact tables in `workspace.walmart_m5_gold`:
# MAGIC
# MAGIC | Fact | Grain |
# MAGIC |---|---|
# MAGIC | `fact_daily_sales` | date × product × store |
# MAGIC | `fact_product_prices` | store × item × Walmart week |
# MAGIC
# MAGIC `sales_value = quantity * sell_price` (null price → null sales_value).

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Configuration
# MAGIC
# MAGIC Optional Free Edition filter: set `START_DATE` / `END_DATE` to limit fact build.
# MAGIC Leave both as `None` for full history (~59M fact rows).

# COMMAND ----------

from pyspark.sql import functions as F

CATALOG = "workspace"
SILVER_SCHEMA = f"{CATALOG}.walmart_m5_silver"
GOLD_SCHEMA = f"{CATALOG}.walmart_m5_gold"

SILVER_SALES = f"{SILVER_SCHEMA}.silver_sales"
SILVER_PRICES = f"{SILVER_SCHEMA}.silver_sell_prices"
SILVER_CALENDAR = f"{SILVER_SCHEMA}.silver_calendar"

DIM_DATE = f"{GOLD_SCHEMA}.dim_date"
DIM_PRODUCT = f"{GOLD_SCHEMA}.dim_product"
DIM_STORE = f"{GOLD_SCHEMA}.dim_store"

FACT_DAILY_SALES = f"{GOLD_SCHEMA}.fact_daily_sales"
FACT_PRODUCT_PRICES = f"{GOLD_SCHEMA}.fact_product_prices"

# Example test window: START_DATE, END_DATE = "2016-01-01", "2016-01-31"
START_DATE = None
END_DATE = None

print(FACT_DAILY_SALES)
print(FACT_PRODUCT_PRICES)
print("Date filter:", START_DATE, "→", END_DATE)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) Ensure Gold schema + dimensions exist

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {GOLD_SCHEMA}")

for table_name in [DIM_DATE, DIM_PRODUCT, DIM_STORE]:
    if not spark.catalog.tableExists(table_name):
        raise ValueError(f"Missing dimension table: {table_name}. Run 05_gold_dimensions first.")
    print("Found:", table_name, "rows=", spark.table(table_name).count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Build `fact_product_prices`
# MAGIC
# MAGIC Attach `product_key` / `store_key` to weekly sell prices.

# COMMAND ----------

prices = spark.table(SILVER_PRICES)
dim_product = spark.table(DIM_PRODUCT).select("product_key", "item_id")
dim_store_keys = spark.table(DIM_STORE).select("store_key", "store_id")

fact_product_prices = (
    prices.join(dim_product, on="item_id", how="inner")
    .join(dim_store_keys, on="store_id", how="inner")
    .select(
        "store_key",
        "product_key",
        "store_id",
        "item_id",
        F.col("wm_yr_wk").cast("int").alias("wm_yr_wk"),
        F.col("sell_price").cast("double").alias("sell_price"),
    )
)

(
    fact_product_prices.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(FACT_PRODUCT_PRICES)
)

print("Wrote:", FACT_PRODUCT_PRICES, "rows=", f"{spark.table(FACT_PRODUCT_PRICES).count():,}")
display(spark.table(FACT_PRODUCT_PRICES).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) Prepare daily sales + price + calendar flags
# MAGIC
# MAGIC Join path:
# MAGIC 1. `silver_sales` → dim keys
# MAGIC 2. weekly `sell_price` on (`store_id`, `item_id`, `wm_yr_wk`)
# MAGIC 3. SNAP flag based on store `state_id`

# COMMAND ----------

sales = spark.table(SILVER_SALES)
if START_DATE:
    sales = sales.where(F.col("date") >= F.lit(START_DATE).cast("date"))
if END_DATE:
    sales = sales.where(F.col("date") <= F.lit(END_DATE).cast("date"))

dim_date = spark.table(DIM_DATE).select(
    "date_key",
    "date",
    "event_flag",
    "snap_CA",
    "snap_TX",
    "snap_WI",
)

# Keep store_key only from dim_store — state_id already exists on silver_sales.
sales_keyed = (
    sales.join(dim_product, on="item_id", how="inner")
    .join(dim_store_keys, on="store_id", how="inner")
    .join(dim_date, on="date", how="inner")
)

price_lookup = spark.table(FACT_PRODUCT_PRICES).select(
    "store_id",
    "item_id",
    "wm_yr_wk",
    "sell_price",
)

fact_daily_sales = (
    sales_keyed.join(
        price_lookup,
        on=["store_id", "item_id", "wm_yr_wk"],
        how="left",
    )
    .withColumn(
        "snap_flag",
        F.when(
            (F.col("state_id") == "CA") & (F.col("snap_CA") == 1), F.lit(1)
        )
        .when((F.col("state_id") == "TX") & (F.col("snap_TX") == 1), F.lit(1))
        .when((F.col("state_id") == "WI") & (F.col("snap_WI") == 1), F.lit(1))
        .otherwise(F.lit(0)),
    )
    .withColumn(
        "sales_value",
        F.round(F.col("quantity").cast("double") * F.col("sell_price"), 4),
    )
    .select(
        "date_key",
        "product_key",
        "store_key",
        "date",
        "item_id",
        "store_id",
        "state_id",
        "dept_id",
        "cat_id",
        "wm_yr_wk",
        "day_id",
        F.col("quantity").cast("int").alias("quantity"),
        F.col("sell_price").cast("double").alias("sell_price"),
        "sales_value",
        F.col("event_flag").cast("int").alias("event_flag"),
        F.col("snap_flag").cast("int").alias("snap_flag"),
    )
)

print("Fact rows (pre-write):", f"{fact_daily_sales.count():,}")
display(fact_daily_sales.limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) Quality checks for `fact_daily_sales`

# COMMAND ----------

checks = {
    "null_date_key": fact_daily_sales.filter(F.col("date_key").isNull()).count(),
    "null_product_key": fact_daily_sales.filter(F.col("product_key").isNull()).count(),
    "null_store_key": fact_daily_sales.filter(F.col("store_key").isNull()).count(),
    "negative_qty": fact_daily_sales.filter(F.col("quantity") < 0).count(),
}

dupes = (
    fact_daily_sales.groupBy("date_key", "product_key", "store_key")
    .count()
    .filter(F.col("count") > 1)
    .count()
)
checks["duplicate_grain"] = dupes

for name, value in checks.items():
    print(f"{name}: {value}")

failed = {k: v for k, v in checks.items() if v > 0}
if failed:
    raise ValueError(f"fact_daily_sales checks failed: {failed}")

priced = fact_daily_sales.filter(F.col("sell_price").isNotNull()).count()
total = fact_daily_sales.count()
print(f"Rows with price: {priced:,} / {total:,} ({priced / total:.1%})")
print("fact_daily_sales quality checks passed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) Write `fact_daily_sales`
# MAGIC
# MAGIC Partitioned by `date` for Power BI / SQL pruning.

# COMMAND ----------

(
    fact_daily_sales.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .partitionBy("date")
    .saveAsTable(FACT_DAILY_SALES)
)

print("Wrote:", FACT_DAILY_SALES)
print("Rows:", f"{spark.table(FACT_DAILY_SALES).count():,}")
display(
    spark.table(FACT_DAILY_SALES)
    .select(
        "date",
        "item_id",
        "store_id",
        "quantity",
        "sell_price",
        "sales_value",
        "event_flag",
        "snap_flag",
    )
    .limit(20)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7) SQL preview

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   MIN(date) AS min_date,
# MAGIC   MAX(date) AS max_date,
# MAGIC   COUNT(*) AS row_count,
# MAGIC   SUM(quantity) AS total_units,
# MAGIC   ROUND(SUM(sales_value), 2) AS total_sales_value
# MAGIC FROM workspace.walmart_m5_gold.fact_daily_sales;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Next: `07_gold_aggregations` for BI-ready aggregate tables.
