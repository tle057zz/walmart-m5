# Databricks notebook source
# MAGIC %md
# MAGIC # 05 — Gold dimensions (Walmart M5)
# MAGIC
# MAGIC Build star-schema dimensions in `workspace.walmart_m5_gold`:
# MAGIC
# MAGIC | Dimension | Source |
# MAGIC |---|---|
# MAGIC | `dim_date` | `silver_calendar` |
# MAGIC | `dim_product` | `silver_products` |
# MAGIC | `dim_store` | `silver_stores` |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Configuration

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

CATALOG = "workspace"
SILVER_SCHEMA = f"{CATALOG}.walmart_m5_silver"
GOLD_SCHEMA = f"{CATALOG}.walmart_m5_gold"

SILVER_CALENDAR = f"{SILVER_SCHEMA}.silver_calendar"
SILVER_PRODUCTS = f"{SILVER_SCHEMA}.silver_products"
SILVER_STORES = f"{SILVER_SCHEMA}.silver_stores"

DIM_DATE = f"{GOLD_SCHEMA}.dim_date"
DIM_PRODUCT = f"{GOLD_SCHEMA}.dim_product"
DIM_STORE = f"{GOLD_SCHEMA}.dim_store"

print(DIM_DATE)
print(DIM_PRODUCT)
print(DIM_STORE)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) Ensure Gold schema exists

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {GOLD_SCHEMA}")
print("Schema ready:", GOLD_SCHEMA)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Build `dim_date`
# MAGIC
# MAGIC Surrogate key: `date_key` as `yyyyMMdd` integer.
# MAGIC Keep calendar attributes needed for BI (events, SNAP, week).

# COMMAND ----------

dim_date = (
    spark.table(SILVER_CALENDAR)
    .select(
        F.date_format("date", "yyyyMMdd").cast("int").alias("date_key"),
        F.col("date"),
        F.col("day_id"),
        F.col("wm_yr_wk"),
        F.col("weekday"),
        F.col("wday"),
        F.col("month"),
        F.col("year"),
        F.col("event_name_1"),
        F.col("event_type_1"),
        F.col("event_name_2"),
        F.col("event_type_2"),
        F.col("event_flag"),
        F.col("snap_CA"),
        F.col("snap_TX"),
        F.col("snap_WI"),
        F.col("snap_any_flag"),
    )
    .dropDuplicates(["date_key"])
)

date_checks = {
    "null_date_key": dim_date.filter(F.col("date_key").isNull()).count(),
    "duplicate_date_key": (
        dim_date.groupBy("date_key").count().filter(F.col("count") > 1).count()
    ),
}
print(date_checks)
if any(date_checks.values()):
    raise ValueError(f"dim_date checks failed: {date_checks}")

(
    dim_date.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(DIM_DATE)
)

print("Wrote:", DIM_DATE, "rows=", spark.table(DIM_DATE).count())
display(spark.table(DIM_DATE).orderBy("date").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) Build `dim_product`
# MAGIC
# MAGIC Surrogate key: dense `product_key` ordered by `item_id`.

# COMMAND ----------

dim_product = (
    spark.table(SILVER_PRODUCTS)
    .withColumn(
        "product_key",
        F.row_number().over(Window.orderBy("item_id")).cast("int"),
    )
    .select(
        "product_key",
        "item_id",
        "dept_id",
        "cat_id",
    )
)

product_checks = {
    "null_product_key": dim_product.filter(F.col("product_key").isNull()).count(),
    "duplicate_item_id": (
        dim_product.groupBy("item_id").count().filter(F.col("count") > 1).count()
    ),
}
print(product_checks)
if any(product_checks.values()):
    raise ValueError(f"dim_product checks failed: {product_checks}")

(
    dim_product.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(DIM_PRODUCT)
)

print("Wrote:", DIM_PRODUCT, "rows=", spark.table(DIM_PRODUCT).count())
display(spark.table(DIM_PRODUCT).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) Build `dim_store`
# MAGIC
# MAGIC Surrogate key: dense `store_key` ordered by `store_id`.

# COMMAND ----------

dim_store = (
    spark.table(SILVER_STORES)
    .withColumn(
        "store_key",
        F.row_number().over(Window.orderBy("store_id")).cast("int"),
    )
    .select(
        "store_key",
        "store_id",
        "state_id",
    )
)

store_checks = {
    "null_store_key": dim_store.filter(F.col("store_key").isNull()).count(),
    "duplicate_store_id": (
        dim_store.groupBy("store_id").count().filter(F.col("count") > 1).count()
    ),
}
print(store_checks)
if any(store_checks.values()):
    raise ValueError(f"dim_store checks failed: {store_checks}")

(
    dim_store.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(DIM_STORE)
)

print("Wrote:", DIM_STORE, "rows=", spark.table(DIM_STORE).count())
display(spark.table(DIM_STORE))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) SQL preview

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'dim_date' AS table_name, COUNT(*) AS row_count FROM workspace.walmart_m5_gold.dim_date
# MAGIC UNION ALL
# MAGIC SELECT 'dim_product', COUNT(*) FROM workspace.walmart_m5_gold.dim_product
# MAGIC UNION ALL
# MAGIC SELECT 'dim_store', COUNT(*) FROM workspace.walmart_m5_gold.dim_store;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Next: `06_gold_facts` → `fact_daily_sales`, `fact_product_prices`.
