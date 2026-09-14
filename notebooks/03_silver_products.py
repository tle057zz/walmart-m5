# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Silver products, stores & prices (Walmart M5)
# MAGIC
# MAGIC Build cleaned dimensional / reference tables from Bronze:
# MAGIC
# MAGIC | Silver table | Source |
# MAGIC |---|---|
# MAGIC | `silver_products` | distinct items from `bronze_sales` |
# MAGIC | `silver_stores` | distinct stores from `bronze_sales` |
# MAGIC | `silver_sell_prices` | cleaned `bronze_sell_prices` |
# MAGIC
# MAGIC Schema: `workspace.walmart_m5_silver`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1) Configuration

# COMMAND ----------

from pyspark.sql import functions as F

CATALOG = "workspace"
BRONZE_SCHEMA = f"{CATALOG}.walmart_m5_bronze"
SILVER_SCHEMA = f"{CATALOG}.walmart_m5_silver"

BRONZE_SALES = f"{BRONZE_SCHEMA}.bronze_sales"
BRONZE_PRICES = f"{BRONZE_SCHEMA}.bronze_sell_prices"

SILVER_PRODUCTS = f"{SILVER_SCHEMA}.silver_products"
SILVER_STORES = f"{SILVER_SCHEMA}.silver_stores"
SILVER_PRICES = f"{SILVER_SCHEMA}.silver_sell_prices"

print(SILVER_PRODUCTS)
print(SILVER_STORES)
print(SILVER_PRICES)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2) Ensure Silver schema exists

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA}")
print("Schema ready:", SILVER_SCHEMA)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3) Build `silver_products`
# MAGIC
# MAGIC Product hierarchy extracted from sales identity columns:
# MAGIC `item_id → dept_id → cat_id`.

# COMMAND ----------

sales_bronze = spark.table(BRONZE_SALES)

silver_products = (
    sales_bronze.select("item_id", "dept_id", "cat_id")
    .where(F.col("item_id").isNotNull())
    .dropDuplicates(["item_id"])
    .withColumn("dept_id", F.col("dept_id").cast("string"))
    .withColumn("cat_id", F.col("cat_id").cast("string"))
    .orderBy("cat_id", "dept_id", "item_id")
)

product_checks = {
    "null_item_id": silver_products.filter(F.col("item_id").isNull()).count(),
    "duplicate_item_id": (
        silver_products.groupBy("item_id").count().filter(F.col("count") > 1).count()
    ),
}
print(product_checks)
if any(product_checks.values()):
    raise ValueError(f"silver_products checks failed: {product_checks}")

(
    silver_products.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(SILVER_PRODUCTS)
)

print("Wrote:", SILVER_PRODUCTS, "rows=", spark.table(SILVER_PRODUCTS).count())
display(spark.table(SILVER_PRODUCTS).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4) Build `silver_stores`
# MAGIC
# MAGIC Store hierarchy: `store_id` + `state_id` (CA / TX / WI in M5).

# COMMAND ----------

silver_stores = (
    sales_bronze.select("store_id", "state_id")
    .where(F.col("store_id").isNotNull())
    .dropDuplicates(["store_id"])
    .withColumn("state_id", F.col("state_id").cast("string"))
    .orderBy("state_id", "store_id")
)

store_checks = {
    "null_store_id": silver_stores.filter(F.col("store_id").isNull()).count(),
    "duplicate_store_id": (
        silver_stores.groupBy("store_id").count().filter(F.col("count") > 1).count()
    ),
}
print(store_checks)
if any(store_checks.values()):
    raise ValueError(f"silver_stores checks failed: {store_checks}")

(
    silver_stores.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(SILVER_STORES)
)

print("Wrote:", SILVER_STORES, "rows=", spark.table(SILVER_STORES).count())
display(spark.table(SILVER_STORES))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5) Build `silver_sell_prices`
# MAGIC
# MAGIC Clean pricing:
# MAGIC - cast types
# MAGIC - keep `sell_price > 0`
# MAGIC - drop exact duplicates

# COMMAND ----------

prices_bronze = spark.table(BRONZE_PRICES)

silver_prices = (
    prices_bronze.select("store_id", "item_id", "wm_yr_wk", "sell_price")
    .withColumn("wm_yr_wk", F.col("wm_yr_wk").cast("int"))
    .withColumn("sell_price", F.col("sell_price").cast("double"))
    .where(
        F.col("store_id").isNotNull()
        & F.col("item_id").isNotNull()
        & F.col("wm_yr_wk").isNotNull()
        & (F.col("sell_price") > 0)
    )
    .dropDuplicates(["store_id", "item_id", "wm_yr_wk"])
)

price_checks = {
    "null_keys": silver_prices.filter(
        F.col("store_id").isNull()
        | F.col("item_id").isNull()
        | F.col("wm_yr_wk").isNull()
    ).count(),
    "non_positive_price": silver_prices.filter(F.col("sell_price") <= 0).count(),
}
print(price_checks)
if any(price_checks.values()):
    raise ValueError(f"silver_sell_prices checks failed: {price_checks}")

(
    silver_prices.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(SILVER_PRICES)
)

print("Wrote:", SILVER_PRICES, "rows=", f"{spark.table(SILVER_PRICES).count():,}")
display(spark.table(SILVER_PRICES).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6) Referential spot-checks
# MAGIC
# MAGIC Confirm price keys exist in product / store dimensions.

# COMMAND ----------

products = spark.table(SILVER_PRODUCTS).select("item_id")
stores = spark.table(SILVER_STORES).select("store_id")
prices = spark.table(SILVER_PRICES)

orphan_items = (
    prices.select("item_id").distinct()
    .join(products, on="item_id", how="left_anti")
    .count()
)
orphan_stores = (
    prices.select("store_id").distinct()
    .join(stores, on="store_id", how="left_anti")
    .count()
)

print("Price item_ids missing from silver_products:", orphan_items)
print("Price store_ids missing from silver_stores:", orphan_stores)

# M5 prices can include items/stores beyond evaluation sales in edge cases;
# warn but do not hard-fail Free Edition runs.
if orphan_items or orphan_stores:
    print("WARNING: orphan price keys found — review before Gold joins")
else:
    print("Referential spot-checks passed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7) SQL preview

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'silver_products' AS table_name, COUNT(*) AS row_count
# MAGIC FROM workspace.walmart_m5_silver.silver_products
# MAGIC UNION ALL
# MAGIC SELECT 'silver_stores', COUNT(*)
# MAGIC FROM workspace.walmart_m5_silver.silver_stores
# MAGIC UNION ALL
# MAGIC SELECT 'silver_sell_prices', COUNT(*)
# MAGIC FROM workspace.walmart_m5_silver.silver_sell_prices;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Next notebook: `04_silver_calendar`.
