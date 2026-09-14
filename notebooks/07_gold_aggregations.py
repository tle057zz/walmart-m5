# Databricks notebook source
# MAGIC %md
# MAGIC # 07 — Gold aggregations (Walmart M5)
# MAGIC
# MAGIC Build BI-ready aggregate tables from Gold facts / dimensions for Power BI.
# MAGIC
# MAGIC | Aggregate | Purpose |
# MAGIC |---|---|
# MAGIC | `agg_daily_store_sales` | store performance by day |
# MAGIC | `agg_daily_category_sales` | category mix by day |
# MAGIC | `agg_store_category_sales` | store × category contribution |
# MAGIC | `agg_product_performance` | SKU ranking / velocity |
# MAGIC | `agg_demand_trends` | rolling demand signals |
# MAGIC | `agg_price_analysis` | price distribution by category |
# MAGIC | `agg_event_sales` | event vs non-event sales |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Configuration

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

CATALOG = "workspace"
GOLD_SCHEMA = f"{CATALOG}.walmart_m5_gold"

FACT_DAILY_SALES = f"{GOLD_SCHEMA}.fact_daily_sales"
DIM_PRODUCT = f"{GOLD_SCHEMA}.dim_product"
DIM_STORE = f"{GOLD_SCHEMA}.dim_store"
DIM_DATE = f"{GOLD_SCHEMA}.dim_date"

AGG_DAILY_STORE = f"{GOLD_SCHEMA}.agg_daily_store_sales"
AGG_DAILY_CATEGORY = f"{GOLD_SCHEMA}.agg_daily_category_sales"
AGG_STORE_CATEGORY = f"{GOLD_SCHEMA}.agg_store_category_sales"
AGG_PRODUCT_PERF = f"{GOLD_SCHEMA}.agg_product_performance"
AGG_DEMAND_TRENDS = f"{GOLD_SCHEMA}.agg_demand_trends"
AGG_PRICE_ANALYSIS = f"{GOLD_SCHEMA}.agg_price_analysis"
AGG_EVENT_SALES = f"{GOLD_SCHEMA}.agg_event_sales"

if not spark.catalog.tableExists(FACT_DAILY_SALES):
    raise ValueError("Missing fact_daily_sales. Run 06_gold_facts first.")

fact = spark.table(FACT_DAILY_SALES)
print("fact_daily_sales rows:", f"{fact.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) `agg_daily_store_sales`

# COMMAND ----------

agg_daily_store = (
    fact.groupBy("date", "date_key", "store_key", "store_id", "state_id")
    .agg(
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("sales_value"), 2).alias("sales_value"),
        F.countDistinct("product_key").alias("active_skus"),
        F.round(F.avg("sell_price"), 4).alias("avg_sell_price"),
    )
)

(
    agg_daily_store.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .partitionBy("date")
    .saveAsTable(AGG_DAILY_STORE)
)
print("Wrote:", AGG_DAILY_STORE, "rows=", f"{spark.table(AGG_DAILY_STORE).count():,}")
display(spark.table(AGG_DAILY_STORE).orderBy(F.desc("date")).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) `agg_daily_category_sales`

# COMMAND ----------

agg_daily_category = (
    fact.groupBy("date", "date_key", "cat_id")
    .agg(
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("sales_value"), 2).alias("sales_value"),
        F.countDistinct("product_key").alias("active_skus"),
        F.countDistinct("store_key").alias("active_stores"),
    )
)

(
    agg_daily_category.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .partitionBy("date")
    .saveAsTable(AGG_DAILY_CATEGORY)
)
print("Wrote:", AGG_DAILY_CATEGORY, "rows=", f"{spark.table(AGG_DAILY_CATEGORY).count():,}")
display(spark.table(AGG_DAILY_CATEGORY).orderBy(F.desc("date")).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) `agg_store_category_sales`

# COMMAND ----------

agg_store_category = (
    fact.groupBy("store_key", "store_id", "state_id", "cat_id")
    .agg(
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("sales_value"), 2).alias("sales_value"),
        F.countDistinct("date").alias("active_days"),
        F.countDistinct("product_key").alias("active_skus"),
    )
)

store_totals = agg_store_category.groupBy("store_key").agg(
    F.sum("sales_value").alias("store_sales_value")
)

agg_store_category = (
    agg_store_category.join(store_totals, on="store_key", how="left")
    .withColumn(
        "category_sales_share",
        F.when(
            F.col("store_sales_value") > 0,
            F.round(F.col("sales_value") / F.col("store_sales_value"), 4),
        ).otherwise(F.lit(None)),
    )
    .drop("store_sales_value")
)

(
    agg_store_category.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(AGG_STORE_CATEGORY)
)
print("Wrote:", AGG_STORE_CATEGORY, "rows=", spark.table(AGG_STORE_CATEGORY).count())
display(spark.table(AGG_STORE_CATEGORY).orderBy("store_id", "cat_id").limit(30))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) `agg_product_performance`

# COMMAND ----------

agg_product_performance = (
    fact.groupBy("product_key", "item_id", "dept_id", "cat_id")
    .agg(
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("sales_value"), 2).alias("sales_value"),
        F.countDistinct("store_key").alias("stores_selling"),
        F.countDistinct("date").alias("days_selling"),
        F.round(F.avg("quantity"), 4).alias("avg_daily_units"),
        F.round(F.stddev_pop("quantity"), 4).alias("demand_volatility"),
        F.round(F.avg("sell_price"), 4).alias("avg_sell_price"),
    )
    .withColumn(
        "units_rank",
        F.dense_rank().over(Window.orderBy(F.desc("units_sold"))),
    )
)

(
    agg_product_performance.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(AGG_PRODUCT_PERF)
)
print("Wrote:", AGG_PRODUCT_PERF, "rows=", spark.table(AGG_PRODUCT_PERF).count())
display(spark.table(AGG_PRODUCT_PERF).orderBy("units_rank").limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) `agg_demand_trends`
# MAGIC
# MAGIC Daily total demand with rolling 7-day and 28-day units.

# COMMAND ----------

daily_demand = (
    fact.groupBy("date", "date_key")
    .agg(
        F.sum("quantity").alias("daily_units"),
        F.round(F.sum("sales_value"), 2).alias("daily_sales_value"),
        F.countDistinct("product_key").alias("active_skus"),
        F.countDistinct("store_key").alias("active_stores"),
    )
)

w7 = Window.orderBy("date").rowsBetween(-6, 0)
w28 = Window.orderBy("date").rowsBetween(-27, 0)

agg_demand_trends = (
    daily_demand.withColumn("rolling_7d_units", F.sum("daily_units").over(w7))
    .withColumn("rolling_28d_units", F.sum("daily_units").over(w28))
    .withColumn(
        "rolling_7d_avg_units",
        F.round(F.col("rolling_7d_units") / F.lit(7.0), 2),
    )
)

(
    agg_demand_trends.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(AGG_DEMAND_TRENDS)
)
print("Wrote:", AGG_DEMAND_TRENDS, "rows=", spark.table(AGG_DEMAND_TRENDS).count())
display(spark.table(AGG_DEMAND_TRENDS).orderBy(F.desc("date")).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7) `agg_price_analysis`

# COMMAND ----------

agg_price_analysis = (
    fact.where(F.col("sell_price").isNotNull())
    .groupBy("cat_id", "dept_id")
    .agg(
        F.count("*").alias("priced_rows"),
        F.round(F.avg("sell_price"), 4).alias("avg_sell_price"),
        F.round(F.min("sell_price"), 4).alias("min_sell_price"),
        F.round(F.max("sell_price"), 4).alias("max_sell_price"),
        F.round(F.percentile_approx("sell_price", 0.5), 4).alias("median_sell_price"),
        F.round(F.sum("sales_value"), 2).alias("sales_value"),
    )
)

(
    agg_price_analysis.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(AGG_PRICE_ANALYSIS)
)
print("Wrote:", AGG_PRICE_ANALYSIS, "rows=", spark.table(AGG_PRICE_ANALYSIS).count())
display(spark.table(AGG_PRICE_ANALYSIS).orderBy("cat_id", "dept_id"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8) `agg_event_sales`
# MAGIC
# MAGIC Compare sales on event days vs non-event days.

# COMMAND ----------

agg_event_sales = (
    fact.groupBy("event_flag", "cat_id")
    .agg(
        F.countDistinct("date").alias("days"),
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("sales_value"), 2).alias("sales_value"),
        F.round(F.avg("quantity"), 4).alias("avg_units_per_row"),
    )
    .withColumn(
        "event_label",
        F.when(F.col("event_flag") == 1, F.lit("event_day")).otherwise(F.lit("non_event_day")),
    )
)

(
    agg_event_sales.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(AGG_EVENT_SALES)
)
print("Wrote:", AGG_EVENT_SALES, "rows=", spark.table(AGG_EVENT_SALES).count())
display(spark.table(AGG_EVENT_SALES).orderBy("cat_id", "event_flag"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9) SQL inventory of Gold aggregates

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'agg_daily_store_sales' AS table_name, COUNT(*) AS row_count FROM workspace.walmart_m5_gold.agg_daily_store_sales
# MAGIC UNION ALL
# MAGIC SELECT 'agg_daily_category_sales', COUNT(*) FROM workspace.walmart_m5_gold.agg_daily_category_sales
# MAGIC UNION ALL
# MAGIC SELECT 'agg_store_category_sales', COUNT(*) FROM workspace.walmart_m5_gold.agg_store_category_sales
# MAGIC UNION ALL
# MAGIC SELECT 'agg_product_performance', COUNT(*) FROM workspace.walmart_m5_gold.agg_product_performance
# MAGIC UNION ALL
# MAGIC SELECT 'agg_demand_trends', COUNT(*) FROM workspace.walmart_m5_gold.agg_demand_trends
# MAGIC UNION ALL
# MAGIC SELECT 'agg_price_analysis', COUNT(*) FROM workspace.walmart_m5_gold.agg_price_analysis
# MAGIC UNION ALL
# MAGIC SELECT 'agg_event_sales', COUNT(*) FROM workspace.walmart_m5_gold.agg_event_sales;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done — Gold layer complete
# MAGIC
# MAGIC Medallion tables now available for BI:
# MAGIC - Dimensions: `dim_date`, `dim_product`, `dim_store`
# MAGIC - Facts: `fact_daily_sales`, `fact_product_prices`
# MAGIC - Aggregates: store / category / product / demand / price / event
# MAGIC
# MAGIC **Suggested next steps:**
# MAGIC 1. Connect Power BI to Databricks SQL Warehouse
# MAGIC 2. Wire Airflow → Databricks Jobs for Bronze/Silver/Gold
# MAGIC 3. Build Executive / Store / Product / Demand dashboards
