# Power BI — Complete DAX + Dashboard Spec (Walmart M5 Gold)

Use tables from `workspace.walmart_m5_gold` (same columns as `data/gold_export/`).

Recommended imported tables:
- `dim_date`, `dim_product`, `dim_store`
- `agg_daily_store_sales`, `agg_daily_category_sales`, `agg_store_category_sales`
- `agg_product_performance`, `agg_demand_trends`, `agg_price_analysis`, `agg_event_sales`

Skip `fact_daily_sales` for Import dashboards (too large). Aggs cover KPIs.

---

## 0) Model setup

### Relationships (`*:1`, cross-filter **Single**)

| From (many) | To (one) |
|---|---|
| `agg_daily_store_sales[date_key]` | `dim_date[date_key]` |
| `agg_daily_category_sales[date_key]` | `dim_date[date_key]` |
| `agg_demand_trends[date_key]` | `dim_date[date_key]` |
| `agg_daily_store_sales[store_key]` | `dim_store[store_key]` |
| `agg_store_category_sales[store_key]` | `dim_store[store_key]` |
| `agg_product_performance[product_key]` | `dim_product[product_key]` |

Optional (if Power BI allows without conflict):
- `agg_store_category_sales` has no date — OK
- `agg_event_sales`, `agg_price_analysis` — often used without dims, or join `cat_id` manually in visuals

Mark as **Date table**: `dim_date[date]` (Table tools → Mark as date table).

### Create a measure table
1. Enter data → one column `Measure` → blank row → Load  
2. Rename table to `_Measures`  
3. Put all measures below in `_Measures`

---

## 1) All DAX measures

Copy/paste each into `_Measures`.

### Core sales (from store daily agg)

```dax
Total Units =
SUM ( 'agg_daily_store_sales'[units_sold] )
```

```dax
Total Sales Value =
SUM ( 'agg_daily_store_sales'[sales_value] )
```

```dax
Avg Sell Price =
AVERAGE ( 'agg_daily_store_sales'[avg_sell_price] )
```

```dax
Active SKUs (Store Day) =
SUM ( 'agg_daily_store_sales'[active_skus] )
```

```dax
Avg Daily Sales Value =
AVERAGEX (
    VALUES ( 'dim_date'[date] ),
    [Total Sales Value]
)
```

### Category

```dax
Category Units =
SUM ( 'agg_daily_category_sales'[units_sold] )
```

```dax
Category Sales Value =
SUM ( 'agg_daily_category_sales'[sales_value] )
```

```dax
Category Active Stores =
SUM ( 'agg_daily_category_sales'[active_stores] )
```

### Product performance

```dax
Product Units =
SUM ( 'agg_product_performance'[units_sold] )
```

```dax
Product Sales Value =
SUM ( 'agg_product_performance'[sales_value] )
```

```dax
Product Avg Daily Units =
AVERAGE ( 'agg_product_performance'[avg_daily_units] )
```

```dax
Product Demand Volatility =
AVERAGE ( 'agg_product_performance'[demand_volatility] )
```

```dax
Product Avg Price =
AVERAGE ( 'agg_product_performance'[avg_sell_price] )
```

```dax
Stores Selling =
SUM ( 'agg_product_performance'[stores_selling] )
```

### Demand trends

```dax
Daily Units =
SUM ( 'agg_demand_trends'[daily_units] )
```

```dax
Daily Sales Value (Demand) =
SUM ( 'agg_demand_trends'[daily_sales_value] )
```

```dax
Rolling 7D Units =
SUM ( 'agg_demand_trends'[rolling_7d_units] )
```

```dax
Rolling 28D Units =
SUM ( 'agg_demand_trends'[rolling_28d_units] )
```

```dax
Rolling 7D Avg Units =
AVERAGE ( 'agg_demand_trends'[rolling_7d_avg_units] )
```

```dax
Active SKUs (Demand) =
SUM ( 'agg_demand_trends'[active_skus] )
```

```dax
Active Stores (Demand) =
SUM ( 'agg_demand_trends'[active_stores] )
```

### Event & price

```dax
Event Units =
SUM ( 'agg_event_sales'[units_sold] )
```

```dax
Event Sales Value =
SUM ( 'agg_event_sales'[sales_value] )
```

```dax
Category Share =
AVERAGE ( 'agg_store_category_sales'[category_sales_share] )
```

```dax
Price Avg =
AVERAGE ( 'agg_price_analysis'[avg_sell_price] )
```

```dax
Price Median =
AVERAGE ( 'agg_price_analysis'[median_sell_price] )
```

### Time intelligence (needs Mark as date table on dim_date)

```dax
Sales Value Previous Year =
CALCULATE (
    [Total Sales Value],
    SAMEPERIODLASTYEAR ( 'dim_date'[date] )
)
```

```dax
Sales Value YoY % =
VAR Curr = [Total Sales Value]
VAR Prev = [Sales Value Previous Year]
RETURN
IF (
    Prev = 0 || ISBLANK ( Prev ),
    BLANK (),
    DIVIDE ( Curr - Prev, Prev )
)
```

```dax
Units Previous Year =
CALCULATE (
    [Total Units],
    SAMEPERIODLASTYEAR ( 'dim_date'[date] )
)
```

```dax
Units YoY % =
VAR Curr = [Total Units]
VAR Prev = [Units Previous Year]
RETURN
IF (
    Prev = 0 || ISBLANK ( Prev ),
    BLANK (),
    DIVIDE ( Curr - Prev, Prev )
)
```

```dax
Sales Value MTD =
TOTALMTD ( [Total Sales Value], 'dim_date'[date] )
```

```dax
Sales Value YTD =
TOTALYTD ( [Total Sales Value], 'dim_date'[date] )
```

### Rank / top products (visual-level also works; measure optional)

```dax
Product Units Rank =
RANKX (
    ALLSELECTED ( 'agg_product_performance'[item_id] ),
    [Product Units],
    ,
    DESC,
    DENSE
)
```

---

## 2) Dashboard pages (build all 4)

Global page slicers (add to every page, sync slicers if desired):
- `dim_date[year]`
- `dim_date[month]`
- `dim_store[state_id]` (where relevant)

---

### Page A — Executive

**Layout**
1. Top row: 4 cards  
2. Middle: demand trend line (wide)  
3. Bottom left: store ranking bar  
4. Bottom right: category sales bar  

| # | Visual | Fields |
|---|---|---|
| 1 | Card | `[Total Units]` |
| 2 | Card | `[Total Sales Value]` format Currency |
| 3 | Card | `[Sales Value YoY %]` format % |
| 4 | Card | `[Avg Daily Sales Value]` |
| 5 | Line chart | X: `agg_demand_trends[date]` · Y: `[Daily Units]`, `[Rolling 7D Units]` |
| 6 | Clustered bar | Y: `dim_store[store_id]` · X: `[Total Sales Value]` |
| 7 | Clustered column | X: `agg_daily_category_sales[cat_id]` · Y: `[Category Sales Value]` |
| 8 | Slicer | `dim_date[year]` |

---

### Page B — Store Performance

| # | Visual | Fields |
|---|---|---|
| 1 | Card | `[Total Sales Value]` |
| 2 | Card | `[Total Units]` |
| 3 | Donut | Legend: `dim_store[state_id]` · Values: `[Total Sales Value]` |
| 4 | Clustered bar | Axis: `dim_store[store_id]` · Values: `[Total Sales Value]` Sort desc |
| 5 | Line chart | X: `agg_daily_store_sales[date]` · Legend: `store_id` · Y: `units_sold` |
| 6 | Matrix | Rows: `store_id` · Columns: `agg_store_category_sales[cat_id]` · Values: `[Category Share]` format % |
| 7 | Table | `store_id`, `state_id`, `[Total Units]`, `[Total Sales Value]`, `[Avg Sell Price]` |
| 8 | Slicer | `dim_store[state_id]`, `dim_date[year]` |

---

### Page C — Product Analysis

| # | Visual | Fields |
|---|---|---|
| 1 | Card | `[Product Units]` |
| 2 | Card | `[Product Sales Value]` |
| 3 | Card | `[Product Demand Volatility]` |
| 4 | Clustered bar (Top 15) | Axis: `agg_product_performance[item_id]` · Values: `[Product Units]` |
| 5 | Filter on visual 4 | `units_rank` is less than or equal to **15** (column filter) OR Top N on `item_id` by `[Product Units]` = 15 |
| 6 | Clustered column | X: `cat_id` · Y: `[Product Sales Value]` |
| 7 | Scatter | X: `avg_daily_units` · Y: `demand_volatility` · Size: `sales_value` · Legend: `cat_id` |
| 8 | Table | From `agg_price_analysis`: `cat_id`, `dept_id`, `avg_sell_price`, `median_sell_price`, `min_sell_price`, `max_sell_price`, `sales_value` |
| 9 | Slicer | `dim_product[cat_id]`, `dim_product[dept_id]` |

---

### Page D — Demand Planning

| # | Visual | Fields |
|---|---|---|
| 1 | Card | `[Daily Units]` |
| 2 | Card | `[Rolling 7D Avg Units]` |
| 3 | Card | `[Rolling 28D Units]` |
| 4 | Line chart | X: `agg_demand_trends[date]` · Y: `daily_units`, `rolling_7d_units`, `rolling_28d_units` |
| 5 | Line + column | X: `date` · Column: `[Daily Sales Value (Demand)]` · Line: `[Active SKUs (Demand)]` |
| 6 | Clustered column | X: `agg_event_sales[event_label]` · Legend: `cat_id` · Y: `[Event Units]` |
| 7 | Table | `event_label`, `cat_id`, `days`, `units_sold`, `sales_value`, `avg_units_per_row` |
| 8 | Slicer | `dim_date[year]`, `dim_date[month]` |

Optional demand KPI cards using filters:
- High volatility products: filter `demand_volatility` top 10%

---

## 3) Formatting checklist

- `[Total Sales Value]`, `[Category Sales Value]`, `[Product Sales Value]` → **Currency** `$`
- `[Sales Value YoY %]`, `[Units YoY %]`, `[Category Share]` → **Percentage** 0.0%
- Large integers → **Whole number** with thousands separator
- Charts: turn on data labels for cards/bars only; keep lines clean
- Use one theme color set (avoid purple default overload)

---

## 4) Build order (do this sequence)

1. Relationships + Mark date table  
2. Create `_Measures` + paste all DAX  
3. Page A Executive  
4. Duplicate page → Page B Store (replace visuals)  
5. Duplicate → Page C Product  
6. Duplicate → Page D Demand  
7. Sync year slicer across pages (View → Sync slicers)  
8. Save as `powerbi/walmart_m5_gold.pbix`

---

## 5) Field cheat-sheet (from gold_export)

```text
dim_date: date_key, date, year, month, weekday, event_flag, snap_*
dim_product: product_key, item_id, dept_id, cat_id
dim_store: store_key, store_id, state_id

agg_daily_store_sales: date, date_key, store_key, store_id, state_id,
  units_sold, sales_value, active_skus, avg_sell_price

agg_daily_category_sales: date, date_key, cat_id,
  units_sold, sales_value, active_skus, active_stores

agg_store_category_sales: store_key, store_id, state_id, cat_id,
  units_sold, sales_value, active_days, active_skus, category_sales_share

agg_product_performance: product_key, item_id, dept_id, cat_id,
  units_sold, sales_value, stores_selling, days_selling,
  avg_daily_units, demand_volatility, avg_sell_price, units_rank

agg_demand_trends: date, date_key, daily_units, daily_sales_value,
  active_skus, active_stores, rolling_7d_units, rolling_28d_units,
  rolling_7d_avg_units

agg_price_analysis: cat_id, dept_id, priced_rows, avg_sell_price,
  min_sell_price, max_sell_price, median_sell_price, sales_value

agg_event_sales: event_flag, cat_id, days, units_sold, sales_value,
  avg_units_per_row, event_label
```
