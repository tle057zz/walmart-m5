# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Silver sales (Walmart M5)
# MAGIC
# MAGIC Transform Bronze sales from **wide** (`d_1`…`d_1941`) to **long** daily facts,
# MAGIC then map `day_id` → `date` using `bronze_calendar`.
# MAGIC
# MAGIC | From | To |
# MAGIC |---|---|
# MAGIC | `workspace.walmart_m5_bronze.bronze_sales` | `workspace.walmart_m5_silver.silver_sales` |
# MAGIC | `workspace.walmart_m5_bronze.bronze_calendar` | used for date mapping |
# MAGIC
# MAGIC Target grain: **one row per item × store × day**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Configuration
# MAGIC
# MAGIC `DAY_LIMIT` lets you test on Free Edition with fewer day columns.
# MAGIC Set to `None` for the full `d_1`…`d_1941` history (~59M rows).

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

CATALOG = "workspace"
BRONZE_SCHEMA = f"{CATALOG}.walmart_m5_bronze"
SILVER_SCHEMA = f"{CATALOG}.walmart_m5_silver"

BRONZE_SALES = f"{BRONZE_SCHEMA}.bronze_sales"
BRONZE_CALENDAR = f"{BRONZE_SCHEMA}.bronze_calendar"
SILVER_SALES = f"{SILVER_SCHEMA}.silver_sales"

# None = all days. Example test: DAY_LIMIT = 28
DAY_LIMIT = None

print("Bronze sales:", BRONZE_SALES)
print("Bronze calendar:", BRONZE_CALENDAR)
print("Silver sales:", SILVER_SALES)
print("DAY_LIMIT:", DAY_LIMIT)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) Ensure Silver schema exists

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA}")
print("Schema ready:", SILVER_SCHEMA)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Read Bronze sales and calendar
# MAGIC
# MAGIC Keep identity columns only; day columns are unpivoted next.

# COMMAND ----------

sales_bronze = spark.table(BRONZE_SALES)
calendar_bronze = spark.table(BRONZE_CALENDAR)

id_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
day_cols = [c for c in sales_bronze.columns if c.startswith("d_")]
day_cols = sorted(day_cols, key=lambda x: int(x.split("_")[1]))

if DAY_LIMIT is not None:
    day_cols = day_cols[: int(DAY_LIMIT)]

print("Sales rows:", sales_bronze.count())
print("Day columns selected:", len(day_cols), day_cols[0], "→", day_cols[-1])
display(sales_bronze.select(*id_cols).limit(5))
display(calendar_bronze.select("d", "date", "wm_yr_wk").limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) Wide → long unpivot
# MAGIC
# MAGIC Convert `d_1, d_2, …` columns into rows:
# MAGIC `day_id` + `quantity`.

# COMMAND ----------

sales_wide = sales_bronze.select(*id_cols, *day_cols)

# Prefer Spark melt; fall back to stack() on older runtimes.
if hasattr(sales_wide, "melt"):
    sales_long = sales_wide.melt(
        ids=id_cols,
        values=day_cols,
        variableColumnName="day_id",
        valueColumnName="quantity",
    )
else:
    stack_parts = ", ".join([f"'{c}', `{c}`" for c in day_cols])
    stack_expr = f"stack({len(day_cols)}, {stack_parts}) as (day_id, quantity)"
    sales_long = sales_wide.select(*id_cols, F.expr(stack_expr))

sales_long = sales_long.withColumn("quantity", F.col("quantity").cast("int"))

print("Long schema:")
sales_long.printSchema()
display(sales_long.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) Map `day_id` → calendar `date`
# MAGIC
# MAGIC Join on `bronze_calendar.d` (values like `d_1`) to attach the real date
# MAGIC and Walmart week id.

# COMMAND ----------

calendar_map = (
    calendar_bronze.select(
        F.col("d").alias("day_id"),
        F.to_date("date").alias("date"),
        F.col("wm_yr_wk").cast("int").alias("wm_yr_wk"),
    )
    .dropDuplicates(["day_id"])
)

silver_sales = (
    sales_long.join(calendar_map, on="day_id", how="left")
    .select(
        "date",
        "day_id",
        "wm_yr_wk",
        "id",
        "item_id",
        "dept_id",
        "cat_id",
        "store_id",
        "state_id",
        "quantity",
    )
)

unmatched = silver_sales.filter(F.col("date").isNull()).count()
print("Rows with no calendar match:", unmatched)
if unmatched > 0:
    raise ValueError("Some day_id values did not match bronze_calendar.d")

display(silver_sales.orderBy("item_id", "store_id", "date").limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) Data-quality checks (Silver sales)
# MAGIC
# MAGIC - `quantity >= 0`
# MAGIC - keys not null
# MAGIC - no duplicate item/store/day rows

# COMMAND ----------

checks = {
    "null_item_id": silver_sales.filter(F.col("item_id").isNull()).count(),
    "null_store_id": silver_sales.filter(F.col("store_id").isNull()).count(),
    "null_date": silver_sales.filter(F.col("date").isNull()).count(),
    "negative_qty": silver_sales.filter(F.col("quantity") < 0).count(),
}

dupes = (
    silver_sales.groupBy("item_id", "store_id", "day_id")
    .count()
    .filter(F.col("count") > 1)
    .count()
)
checks["duplicate_item_store_day"] = dupes

for name, value in checks.items():
    print(f"{name}: {value}")

failed = {k: v for k, v in checks.items() if v > 0}
if failed:
    raise ValueError(f"silver_sales quality checks failed: {failed}")

print("silver_sales quality checks passed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7) Write `silver_sales`
# MAGIC
# MAGIC Overwrite Delta table, partitioned by `date` for downstream pruning.

# COMMAND ----------

(
    silver_sales.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .partitionBy("date")
    .saveAsTable(SILVER_SALES)
)

row_count = spark.table(SILVER_SALES).count()
print("Wrote:", SILVER_SALES)
print("Rows:", f"{row_count:,}")
display(spark.table(SILVER_SALES).limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8) SQL preview

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   MIN(date) AS min_date,
# MAGIC   MAX(date) AS max_date,
# MAGIC   COUNT(*) AS row_count,
# MAGIC   SUM(quantity) AS total_units
# MAGIC FROM workspace.walmart_m5_silver.silver_sales;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Next notebook: `03_silver_products` (product / store dims + cleaned prices).
