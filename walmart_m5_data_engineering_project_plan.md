# Walmart M5 Retail & Supply Chain Data Engineering Project

## 1. Project Title

**End-to-End FMCG Retail Demand & Supply Planning Data Platform using Apache Airflow, PySpark, Databricks and Power BI**

---

## 2. Project Objective

Build an end-to-end data engineering platform using the Walmart M5 retail dataset.

The project will simulate a production-style FMCG retail analytics pipeline that:

- Ingests raw retail data
- Orchestrates pipelines with Apache Airflow
- Processes large datasets using PySpark
- Stores data using a Bronze / Silver / Gold Medallion Architecture in Databricks
- Performs data-quality checks
- Builds dimensional and aggregated analytical tables
- Connects curated data to Power BI
- Produces retail, product, promotion, demand-planning and supply-chain dashboards

The project is intended to demonstrate practical skills relevant to:

- Data Engineering
- Retail Analytics
- FMCG Analytics
- Supply Chain Analytics
- Demand Planning
- Business Intelligence

---

## 3. Dataset

### Walmart M5 Forecasting - Accuracy

Source:

**Kaggle Competition:** `m5-forecasting-accuracy`

Main files:

```text
calendar.csv
sales_train_evaluation.csv
sales_train_validation.csv
sell_prices.csv
sample_submission.csv
```

For this project, the main source files will be:

```text
calendar.csv
sales_train_evaluation.csv
sell_prices.csv
```

### Why use `sales_train_evaluation.csv`?

`sales_train_evaluation.csv` contains the complete sales history required for the project.

`sales_train_validation.csv` contains an earlier subset of the same historical data, so it is not necessary as the main production source.

`sample_submission.csv` is mainly intended for the forecasting competition and is not required for the core data engineering pipeline.

---

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Source ingestion, utilities, validation scripts |
| Apache Airflow | Pipeline orchestration, dependencies, retries and scheduling |
| Apache Spark / PySpark | Distributed transformations |
| Databricks | Lakehouse platform and processing environment |
| Delta Lake | Bronze, Silver and Gold table storage |
| Databricks SQL | Analytical queries and serving layer |
| Power BI | Dashboards, DAX and business analytics |
| Git / GitHub | Version control and portfolio documentation |

---

## 5. High-Level Architecture

```text
Walmart M5 Raw Dataset
        |
        v
Python Ingestion
        |
        v
Apache Airflow
        |
        v
Databricks
        |
        +-----------------------------+
        |                             |
        v                             |
     BRONZE                           |
 Raw Delta Tables                     |
        |                             |
        v                             |
      PySpark ------------------------+
        |
        v
     SILVER
Clean / Standardized Data
        |
        v
      GOLD
Business / Analytical Tables
        |
        v
Databricks SQL
        |
        v
     Power BI
```

---

## 6. Proposed Repository Structure

```text
walmart-m5-data-engineering/
│
├── airflow/
│   ├── dags/
│   │   └── m5_pipeline_dag.py
│   └── plugins/
│
├── data/
│   └── raw/
│       ├── calendar.csv
│       ├── sales_train_evaluation.csv
│       └── sell_prices.csv
│
├── notebooks/
│   ├── 01_bronze_ingestion.py
│   ├── 02_silver_sales.py
│   ├── 03_silver_products.py
│   ├── 04_silver_calendar.py
│   ├── 05_gold_dimensions.py
│   ├── 06_gold_facts.py
│   └── 07_gold_aggregations.py
│
├── src/
│   ├── ingestion/
│   ├── validation/
│   ├── transformations/
│   └── utils/
│
├── sql/
│   ├── quality_checks/
│   └── analytics/
│
├── powerbi/
│   └── documentation/
│
├── tests/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# 7. Pipeline Design

## Stage 1 - Raw Data Ingestion

Raw files:

```text
calendar.csv
sales_train_evaluation.csv
sell_prices.csv
```

Python will be used to:

- Detect source files
- Validate file availability
- Check basic schema
- Check file size
- Generate ingestion metadata
- Trigger downstream Databricks jobs through Airflow

Possible metadata fields:

```text
_ingestion_timestamp
_source_file
_batch_id
_ingestion_date
```

---

# 8. Apache Airflow Orchestration

Airflow will control the complete pipeline.

Proposed DAG:

```text
start
  |
  v
check_source_files
  |
  v
validate_raw_files
  |
  +-----------------------+
  |           |           |
  v           v           v
load_sales  load_prices  load_calendar
  |           |           |
  +-----------+-----------+
              |
              v
       validate_bronze
              |
              v
      transform_silver
              |
              v
       validate_silver
              |
              v
         build_gold
              |
              v
      run_quality_checks
              |
              v
      publish_analytics
              |
              v
             end
```

### Airflow Concepts Demonstrated

- DAG creation
- Task dependencies
- Scheduling
- Retry logic
- Failure handling
- Logging
- Task grouping
- Databricks job triggering
- Data-quality gates

---

# 9. Databricks Medallion Architecture

## Bronze Layer

Purpose:

Store raw data with minimal modification.

Proposed Bronze tables:

```text
bronze_sales
bronze_calendar
bronze_sell_prices
```

The Bronze layer should preserve original source information while adding ingestion metadata.

Example:

```text
bronze_sales
--------------------------
item_id
dept_id
cat_id
store_id
state_id
d_1
d_2
...
d_1941
_ingestion_timestamp
_source_file
_batch_id
```

---

# 10. Silver Layer

Purpose:

Clean, standardize and normalize the raw data.

One of the most important transformations is converting the M5 sales table from wide format:

```text
item_id | store_id | d_1 | d_2 | d_3 | ...
```

into long format:

```text
item_id | store_id | day_id | quantity
```

This will make downstream analytics significantly easier.

Proposed Silver tables:

```text
silver_sales
silver_products
silver_stores
silver_calendar
silver_sell_prices
```

### `silver_sales`

Possible columns:

```text
date
day_id
item_id
dept_id
cat_id
store_id
state_id
quantity
```

### `silver_sell_prices`

Possible columns:

```text
store_id
item_id
wm_yr_wk
sell_price
```

### `silver_calendar`

Possible columns:

```text
date
wm_yr_wk
weekday
month
year
event_name_1
event_type_1
event_name_2
event_type_2
snap_CA
snap_TX
snap_WI
```

### Silver Transformations

PySpark will handle:

- Data-type conversion
- Null-value handling
- Duplicate detection
- Schema validation
- Wide-to-long transformation
- Date mapping
- Product hierarchy extraction
- Store hierarchy extraction
- Sales-price joins
- Calendar joins
- Event enrichment
- SNAP enrichment

---

# 11. Data Quality Checks

Examples:

### Sales

```text
quantity >= 0
item_id IS NOT NULL
store_id IS NOT NULL
date IS NOT NULL
```

### Price

```text
sell_price > 0
item_id IS NOT NULL
store_id IS NOT NULL
wm_yr_wk IS NOT NULL
```

### Referential Integrity

Check that:

```text
sales.item_id exists in products
sales.store_id exists in stores
sales.date exists in calendar
```

Additional checks:

- Duplicate rows
- Unexpected schema changes
- Missing dates
- Missing prices
- Invalid category values
- Row-count anomalies

---

# 12. Gold Layer

The Gold layer will contain business-ready dimensional and aggregated tables.

## Dimensions

```text
dim_date
dim_product
dim_store
```

## Fact Tables

```text
fact_daily_sales
fact_product_prices
```

## Aggregated Tables

```text
agg_daily_store_sales
agg_daily_category_sales
agg_store_category_sales
agg_product_performance
agg_demand_trends
agg_price_analysis
agg_event_sales
```

---

# 13. Proposed Star Schema

```text
                 dim_date
                    |
                    |
dim_product --- fact_daily_sales --- dim_store
                    |
                    |
             fact_product_prices
```

Example `fact_daily_sales`:

```text
date_key
product_key
store_key
quantity
sell_price
sales_value
event_flag
snap_flag
```

Calculated field:

```text
sales_value = quantity * sell_price
```

---

# 14. Retail and FMCG KPIs

## Sales KPIs

```text
Total Units Sold
Estimated Sales Revenue
Average Daily Sales
Sales Growth %
Average Selling Price
Active SKUs
Active Stores
```

---

## Product KPIs

```text
Top Selling SKUs
Bottom Selling SKUs
Category Contribution %
Department Contribution %
Fast-Moving Products
Slow-Moving Products
Product Demand Volatility
```

---

## Store KPIs

```text
Sales by Store
Store Ranking
Sales by State
Average Daily Store Demand
Category Mix by Store
Store Growth %
```

---

# 15. Supply Chain and Demand Planning KPIs

Because the M5 dataset does not contain actual warehouse inventory, supplier lead times or shipment records, the supply-chain section should focus on demand planning rather than pretending inventory fields magically exist.

Potential metrics:

```text
Daily Demand
Weekly Demand
Rolling 7-Day Demand
Rolling 28-Day Demand
Demand Growth
Demand Volatility
Demand Spike Detection
Fast-Moving SKU Identification
Slow-Moving SKU Identification
Replenishment Priority Indicator
```

---

# 16. Forecasting Extension

Forecasting can be added after the core data engineering pipeline is complete.

Potential techniques:

- Moving average
- Exponential smoothing
- Prophet
- Spark ML
- Machine-learning regression
- Time-series forecasting

Potential output table:

```text
gold_demand_forecast
```

Possible columns:

```text
date
store_id
item_id
actual_demand
forecast_demand
forecast_error
absolute_error
```

Possible metrics:

```text
MAE
RMSE
MAPE
Forecast Accuracy
```

Forecasting is an extension rather than the core requirement of the data engineering project.

---

# 17. Power BI Dashboard Plan

## Dashboard 1 - Executive Retail Overview

KPIs:

```text
Total Units Sold
Estimated Revenue
Sales Growth
Active Stores
Active SKUs
Average Selling Price
```

Visuals:

- Sales trend
- Sales by state
- Sales by category
- Sales by department
- Top stores
- Top products

Filters:

```text
Date
State
Store
Category
Department
Product
```

---

## Dashboard 2 - Store Performance

KPIs:

```text
Store Sales
Average Daily Demand
Store Growth
Active Products
```

Visuals:

- Store ranking
- Store sales trend
- Sales by category
- State comparison
- Store-category matrix
- Store demand volatility

---

## Dashboard 3 - Product & Category Performance

KPIs:

```text
Category Sales
SKU Sales
Category Growth
Average Product Price
Product Contribution
```

Visuals:

- Product ranking
- Category contribution
- Department contribution
- Fast-moving products
- Slow-moving products
- Price vs demand
- Product demand trend

---

## Dashboard 4 - Demand & Supply Planning

KPIs:

```text
Average Daily Demand
7-Day Demand
28-Day Demand
Demand Volatility
High-Demand SKUs
Replenishment Priority
```

Visuals:

- Daily demand trend
- Rolling demand
- SKU demand heatmap
- Store × SKU matrix
- Demand spike alerts
- Volatile product ranking
- Replenishment priority table

If forecasting is implemented:

```text
Actual vs Forecast Demand
Forecast Accuracy
Forecast Error
High Forecast Error Products
```

---

# 18. Suggested Development Phases

## Phase 1 - Environment Setup

- Download Walmart M5 dataset
- Create GitHub repository
- Install Python dependencies
- Set up Apache Airflow
- Set up Databricks workspace
- Create Databricks catalog / schema
- Establish repository structure

---

## Phase 2 - Raw Ingestion

- Create Python source-validation script
- Build Airflow DAG
- Load files into Bronze tables
- Add ingestion metadata
- Test retries and failures

---

## Phase 3 - Silver Transformations

- Transform sales data from wide to long format
- Clean calendar data
- Clean pricing data
- Build product dimension source
- Build store dimension source
- Join calendar information
- Join selling prices
- Run quality checks

---

## Phase 4 - Gold Data Model

Build:

```text
dim_date
dim_product
dim_store
fact_daily_sales
fact_product_prices
```

Then create aggregation tables for Power BI.

---

## Phase 5 - Power BI

- Connect Power BI to Databricks
- Build relationships
- Create DAX measures
- Create Executive dashboard
- Create Store dashboard
- Create Product dashboard
- Create Demand Planning dashboard

---

## Phase 6 - Advanced Engineering

Potential improvements:

- Incremental ingestion
- Delta MERGE
- Partitioning
- Z-Ordering / clustering
- Airflow retry policies
- Audit logging
- Schema drift detection
- Data-quality framework
- Pipeline monitoring
- Slowly Changing Dimensions
- Unit testing
- CI/CD

---

## Phase 7 - Forecasting Extension

Optional:

- Generate demand forecast
- Compare actual vs predicted demand
- Calculate forecast errors
- Feed forecast results into Power BI

---

# 19. Portfolio Story

The final project should communicate the following story:

> A production-style retail data platform was developed using Apache Airflow, PySpark, Databricks, Delta Lake and Power BI to process Walmart M5 FMCG retail data. The platform implements automated ingestion, Medallion Architecture, distributed transformations, data-quality validation, dimensional modelling and business intelligence reporting. The resulting analytical layer supports sales analysis, product and store performance monitoring, demand planning and replenishment prioritisation.

---

# 20. Skills Demonstrated

By completing the project, the portfolio will demonstrate:

### Data Engineering

- ETL / ELT
- Data ingestion
- Pipeline orchestration
- Apache Airflow
- PySpark
- Databricks
- Delta Lake
- Medallion Architecture
- Data quality
- Dimensional modelling
- Fact and dimension tables
- Incremental processing

### Analytics

- Retail analytics
- FMCG analytics
- Demand analysis
- Supply planning
- KPI development
- Power BI
- DAX
- Dashboard design

### Engineering Practices

- Git
- Modular repository structure
- Logging
- Error handling
- Testing
- Documentation
- Production-style architecture

---

# 21. Final Architecture Summary

```text
                       Walmart M5
                           |
                           v
                    Python Ingestion
                           |
                           v
                     Apache Airflow
                           |
                           v
                  Databricks / Delta
                           |
              +------------+------------+
              |                         |
              v                         |
           BRONZE                       |
         Raw Tables                     |
              |                         |
              v                         |
           PySpark ---------------------+
              |
              v
           SILVER
      Clean / Conformed Data
              |
              v
            GOLD
     Star Schema + Aggregates
              |
              v
        Databricks SQL
              |
              v
           Power BI
              |
     +--------+---------+---------+
     |                  |         |
 Executive          Product    Demand /
 Dashboard          Analysis   Supply Planning
```

---

# 22. Immediate Next Step

After downloading the dataset, the first implementation task should be:

1. Create the project repository structure.
2. Place the three source CSV files inside `data/raw/`.
3. Inspect schemas and row counts.
4. Design Bronze Delta tables.
5. Build the first Python ingestion and validation script.
6. Create the initial Airflow DAG.
7. Trigger Bronze ingestion into Databricks.

The first production milestone is:

> **Raw Walmart M5 files successfully ingested into Databricks Bronze Delta tables through an Airflow-orchestrated pipeline.**
