# Power BI — Exact field map (table.column per visual)

Use this while building. Notation:

- `table[column]` = drag from that table
- `[Measure Name]` = drag from `_Measures`
- Well names match Power BI Desktop (Axis / Legend / Values / Rows / Columns / Tooltips)

---

# PAGE 1 — Executive

## Layout
```
[ year slicer ]
[ Card ] [ Card ] [ Card ] [ Card ]
[──────────── Line chart (wide) ────────────]
[ Clustered bar (left) ] [ Clustered column (right) ]
```

## Visual 1 — Slicer: Year

| Well | Table | Column / measure |
|---|---|---|
| Field | `dim_date` | `year` |

## Visual 2 — Card: Total Units

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Total Units]` |

Source behind measure: `SUM(agg_daily_store_sales[units_sold])`

## Visual 3 — Card: Total Sales Value

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Total Sales Value]` |

Source: `SUM(agg_daily_store_sales[sales_value])` · format `$`

## Visual 4 — Card: Sales Value YoY %

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Sales Value YoY %]` |

Needs `dim_date` marked as date table · format `%`

## Visual 5 — Card: Avg Daily Sales Value

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Avg Daily Sales Value]` |

## Visual 6 — Line chart: Demand trend

| Well | Table | Column / measure |
|---|---|---|
| X-axis | `agg_demand_trends` | `date` |
| Y-axis | `_Measures` | `[Daily Units]` |
| Y-axis | `_Measures` | `[Rolling 7D Units]` |
| Legend | *(empty)* | — |

Optional instead of measures (same result):
- Y-axis: `agg_demand_trends[daily_units]`
- Y-axis: `agg_demand_trends[rolling_7d_units]`

## Visual 7 — Clustered bar: Sales by store

| Well | Table | Column / measure |
|---|---|---|
| Y-axis | `dim_store` | `store_id` |
| X-axis | `_Measures` | `[Total Sales Value]` |
| Legend | *(empty)* | — |

Sort: by `[Total Sales Value]` descending

## Visual 8 — Clustered column: Sales by category

| Well | Table | Column / measure |
|---|---|---|
| X-axis | `agg_daily_category_sales` | `cat_id` |
| Y-axis | `_Measures` | `[Category Sales Value]` |
| Legend | *(empty)* | — |

---

# PAGE 2 — Store

## Layout
```
[ state slicer ] [ year slicer ]
[ Card ] [ Card ] [ Donut ]
[ Clustered bar — store ranking ]
[ Line chart — daily by store ]
[ Matrix — category share ]
[ Table — store summary ]
```

## Visual 1 — Slicer: State

| Well | Table | Column / measure |
|---|---|---|
| Field | `dim_store` | `state_id` |

## Visual 2 — Slicer: Year

| Well | Table | Column / measure |
|---|---|---|
| Field | `dim_date` | `year` |

## Visual 3 — Card: Total Sales Value

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Total Sales Value]` |

## Visual 4 — Card: Total Units

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Total Units]` |

## Visual 5 — Donut: Sales by state

| Well | Table | Column / measure |
|---|---|---|
| Legend | `dim_store` | `state_id` |
| Values | `_Measures` | `[Total Sales Value]` |

## Visual 6 — Clustered bar: Store ranking

| Well | Table | Column / measure |
|---|---|---|
| Y-axis | `dim_store` | `store_id` |
| X-axis | `_Measures` | `[Total Sales Value]` |

Sort descending by `[Total Sales Value]`

## Visual 7 — Line chart: Daily units by store

| Well | Table | Column / measure |
|---|---|---|
| X-axis | `agg_daily_store_sales` | `date` |
| Legend | `agg_daily_store_sales` | `store_id` |
| Y-axis | `agg_daily_store_sales` | `units_sold` |

Do **not** mix `dim_store[store_id]` on legend here unless needed — use the column on the agg table for a clean series.

Optional filter on this visual only: `agg_daily_store_sales[store_id]` is `CA_1`, `CA_2`, `TX_1` (reduce clutter).

## Visual 8 — Matrix: Category share by store

| Well | Table | Column / measure |
|---|---|---|
| Rows | `agg_store_category_sales` | `store_id` |
| Columns | `agg_store_category_sales` | `cat_id` |
| Values | `_Measures` | `[Category Share]` |

Format `[Category Share]` as `%`  
Alternative Values (same numbers): `agg_store_category_sales[category_sales_share]`

Optional extra row field: `agg_store_category_sales[state_id]` above `store_id`

## Visual 9 — Table: Store summary

| Column order | Table | Column / measure |
|---|---|---|
| 1 | `dim_store` | `store_id` |
| 2 | `dim_store` | `state_id` |
| 3 | `_Measures` | `[Total Units]` |
| 4 | `_Measures` | `[Total Sales Value]` |
| 5 | `_Measures` | `[Avg Sell Price]` |

---

# PAGE 3 — Product

## Layout
```
[ cat_id slicer ] [ dept_id slicer ]
[ Card ] [ Card ] [ Card ]
[ Clustered bar — Top 15 items ]
[ Clustered column — by category ]
[ Scatter — volatility ]
[ Table — price analysis ]
```

## Visual 1 — Slicer: Category

| Well | Table | Column / measure |
|---|---|---|
| Field | `dim_product` | `cat_id` |

## Visual 2 — Slicer: Department

| Well | Table | Column / measure |
|---|---|---|
| Field | `dim_product` | `dept_id` |

## Visual 3 — Card: Product Units

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Product Units]` |

Source: `SUM(agg_product_performance[units_sold])`

## Visual 4 — Card: Product Sales Value

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Product Sales Value]` |

## Visual 5 — Card: Product Demand Volatility

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Product Demand Volatility]` |

## Visual 6 — Clustered bar: Top 15 products

| Well | Table | Column / measure |
|---|---|---|
| Y-axis | `agg_product_performance` | `item_id` |
| X-axis | `_Measures` | `[Product Units]` |
| Legend | *(empty)* | — |

**Filters on this visual**

| Filter field | Table | Operator | Value |
|---|---|---|---|
| `units_rank` | `agg_product_performance` | is less than or equal to | `15` |

Sort by `[Product Units]` descending

Optional tooltip fields:
- `agg_product_performance[cat_id]`
- `agg_product_performance[dept_id]`
- `agg_product_performance[avg_daily_units]`
- `agg_product_performance[demand_volatility]`

## Visual 7 — Clustered column: Product sales by category

| Well | Table | Column / measure |
|---|---|---|
| X-axis | `agg_product_performance` | `cat_id` |
| Y-axis | `_Measures` | `[Product Sales Value]` |

Or X-axis: `dim_product[cat_id]` (same if relationship is correct)

## Visual 8 — Scatter: Volatility vs volume

| Well | Table | Column / measure |
|---|---|---|
| X-axis | `agg_product_performance` | `avg_daily_units` |
| Y-axis | `agg_product_performance` | `demand_volatility` |
| Size | `agg_product_performance` | `sales_value` |
| Legend | `agg_product_performance` | `cat_id` |
| Values / Details (optional) | `agg_product_performance` | `item_id` |

If scatter asks for “Values”, put `item_id` there so each bubble = one SKU.

## Visual 9 — Table: Price analysis

| Column order | Table | Column / measure |
|---|---|---|
| 1 | `agg_price_analysis` | `cat_id` |
| 2 | `agg_price_analysis` | `dept_id` |
| 3 | `agg_price_analysis` | `avg_sell_price` |
| 4 | `agg_price_analysis` | `median_sell_price` |
| 5 | `agg_price_analysis` | `min_sell_price` |
| 6 | `agg_price_analysis` | `max_sell_price` |
| 7 | `agg_price_analysis` | `sales_value` |
| 8 (optional) | `agg_price_analysis` | `priced_rows` |

No measures required on this table — all columns from `agg_price_analysis`.

---

# PAGE 4 — Demand

## Layout
```
[ year slicer ] [ month slicer ]
[ Card ] [ Card ] [ Card ]
[──────── Line chart rolling demand (wide) ────────]
[ Line and clustered column ]
[ Clustered column — events ]
[ Table — event detail ]
```

## Visual 1 — Slicer: Year

| Well | Table | Column / measure |
|---|---|---|
| Field | `dim_date` | `year` |

## Visual 2 — Slicer: Month

| Well | Table | Column / measure |
|---|---|---|
| Field | `dim_date` | `month` |

## Visual 3 — Card: Daily Units

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Daily Units]` |

Source: `SUM(agg_demand_trends[daily_units])`

## Visual 4 — Card: Rolling 7D Avg Units

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Rolling 7D Avg Units]` |

## Visual 5 — Card: Rolling 28D Units

| Well | Table | Column / measure |
|---|---|---|
| Fields | `_Measures` | `[Rolling 28D Units]` |

## Visual 6 — Line chart: Daily vs rolling demand

| Well | Table | Column / measure |
|---|---|---|
| X-axis | `agg_demand_trends` | `date` |
| Y-axis | `agg_demand_trends` | `daily_units` |
| Y-axis | `agg_demand_trends` | `rolling_7d_units` |
| Y-axis | `agg_demand_trends` | `rolling_28d_units` |

Or use measures instead of columns:
- `[Daily Units]`, `[Rolling 7D Units]`, `[Rolling 28D Units]`

## Visual 7 — Line and clustered column: Sales vs active SKUs

| Well | Table | Column / measure |
|---|---|---|
| X-axis | `agg_demand_trends` | `date` |
| Column y-axis | `_Measures` | `[Daily Sales Value (Demand)]` |
| Line y-axis | `_Measures` | `[Active SKUs (Demand)]` |

Column alternative: `agg_demand_trends[daily_sales_value]`  
Line alternative: `agg_demand_trends[active_skus]`

## Visual 8 — Clustered column: Event impact

| Well | Table | Column / measure |
|---|---|---|
| X-axis | `agg_event_sales` | `event_label` |
| Legend | `agg_event_sales` | `cat_id` |
| Y-axis | `_Measures` | `[Event Units]` |

Y-axis alternative: `agg_event_sales[units_sold]`

## Visual 9 — Table: Event sales detail

| Column order | Table | Column / measure |
|---|---|---|
| 1 | `agg_event_sales` | `event_label` |
| 2 | `agg_event_sales` | `cat_id` |
| 3 | `agg_event_sales` | `days` |
| 4 | `agg_event_sales` | `units_sold` |
| 5 | `agg_event_sales` | `sales_value` |
| 6 | `agg_event_sales` | `avg_units_per_row` |
| 7 (optional) | `agg_event_sales` | `event_flag` |

---

# Quick reference — which table feeds which page

| Page | Primary tables used on canvas |
|---|---|
| Executive | `dim_date`, `dim_store`, `agg_demand_trends`, `agg_daily_category_sales` + measures from `agg_daily_store_sales` |
| Store | `dim_date`, `dim_store`, `agg_daily_store_sales`, `agg_store_category_sales` |
| Product | `dim_product`, `agg_product_performance`, `agg_price_analysis` |
| Demand | `dim_date`, `agg_demand_trends`, `agg_event_sales` |

| Measure group | Built from table |
|---|---|
| Total Units / Sales / Avg Sell Price / Avg Daily Sales | `agg_daily_store_sales` (+ `dim_date` for daily avg / YoY) |
| Category Units / Sales | `agg_daily_category_sales` |
| Product * | `agg_product_performance` |
| Daily / Rolling / Active SKUs (Demand) | `agg_demand_trends` |
| Event * | `agg_event_sales` |
| Category Share | `agg_store_category_sales` |
| Price Avg / Median | `agg_price_analysis` |

---

# Common mistakes

1. Putting `dim_date[date]` on a visual that should use `agg_demand_trends[date]` — both work if related; prefer the agg’s `date` for demand charts.
2. Using `[Total Units]` on Product page Top 15 — wrong grain; use `[Product Units]` / `agg_product_performance`.
3. Connecting `agg_event_sales` to dims when not needed — leave unconnected; use its own columns.
4. Matrix Rows from `dim_store[store_id]` and Columns from `agg_store_category_sales[cat_id]` without Values from the same agg path — prefer all matrix fields from `agg_store_category_sales` (+ measure).
