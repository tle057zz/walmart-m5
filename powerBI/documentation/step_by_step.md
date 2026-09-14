# Power BI — Step-by-step build

Follow in order. Full DAX text is in `dax_and_dashboards.md` in this folder.

---

## Step 1 — Open Power BI Desktop

1. Open **Power BI Desktop**.
2. Start a blank report (or continue your existing Databricks connection file).
3. Save early: **File → Save As** → `powerbi/walmart_m5_gold.pbix`.

---

## Step 2 — Get Gold tables (Import)

1. **Home → Get data → Databricks** (or Azure Databricks).
2. Enter your workspace host + SQL Warehouse HTTP path (Serverless Starter Warehouse).
3. Sign in with PAT / Azure AD as you already did.
4. In Navigator, expand `workspace` → `walmart_m5_gold`.
5. Check these **10 tables only** (Import mode):

   - `dim_date`
   - `dim_product`
   - `dim_store`
   - `agg_daily_store_sales`
   - `agg_daily_category_sales`
   - `agg_store_category_sales`
   - `agg_product_performance`
   - `agg_demand_trends`
   - `agg_price_analysis`
   - `agg_event_sales`

6. Do **not** import `fact_daily_sales` or `fact_product_prices` for this dashboard.
7. Click **Load** (or Transform if you need to set types, then Close & Apply).

Wait until all tables finish loading.

---

## Step 3 — Fix relationships

1. Go to **Model** view (left sidebar).
2. Delete any auto-created wrong relationships (especially `1:1` or **Both** directions).
3. Create these relationships one by one (drag many → one):

| From (many side) | To (one side) |
|---|---|
| `agg_daily_store_sales[date_key]` | `dim_date[date_key]` |
| `agg_daily_category_sales[date_key]` | `dim_date[date_key]` |
| `agg_demand_trends[date_key]` | `dim_date[date_key]` |
| `agg_daily_store_sales[store_key]` | `dim_store[store_key]` |
| `agg_store_category_sales[store_key]` | `dim_store[store_key]` |
| `agg_product_performance[product_key]` | `dim_product[product_key]` |

4. For **each** relationship card:
   - Cardinality: **Many to one (`*:1`)**
   - Cross filter direction: **Single**
   - Make sure “Assume referential integrity” can stay off

5. Leave `agg_price_analysis` and `agg_event_sales` unconnected for now (use their own columns in visuals).

---

## Step 4 — Mark date table

1. Still in Model view, click `dim_date`.
2. **Table tools → Mark as date table → Mark as date table**.
3. Choose column: `date`.
4. OK.

---

## Step 5 — Create `_Measures` table

1. **Home → Enter data**.
2. Rename column to `Measure`.
3. Leave one blank row → **Load**.
4. In Data/Fields pane, rename the new table to `_Measures`.
5. Hide the `Measure` column (right-click → Hide).

---

## Step 6 — Add DAX measures (batch)

Open `powerbi/documentation/dax_and_dashboards.md` and paste measures into `_Measures`.

**How to add one measure**
1. Right-click `_Measures` → **New measure**.
2. Paste the DAX (including the name before `=`).
3. Enter / checkmark.
4. Format in the ribbon:
   - Currency for sales value measures
   - Percentage for YoY % and Category Share

**Add in this order (so dependencies exist first)**

**Batch A — core**
1. `Total Units`
2. `Total Sales Value`
3. `Avg Sell Price`
4. `Active SKUs (Store Day)`
5. `Avg Daily Sales Value`

**Batch B — category**
6. `Category Units`
7. `Category Sales Value`
8. `Category Active Stores`

**Batch C — product**
9. `Product Units`
10. `Product Sales Value`
11. `Product Avg Daily Units`
12. `Product Demand Volatility`
13. `Product Avg Price`
14. `Stores Selling`
15. `Product Units Rank`

**Batch D — demand**
16. `Daily Units`
17. `Daily Sales Value (Demand)`
18. `Rolling 7D Units`
19. `Rolling 28D Units`
20. `Rolling 7D Avg Units`
21. `Active SKUs (Demand)`
22. `Active Stores (Demand)`

**Batch E — event / price**
23. `Event Units`
24. `Event Sales Value`
25. `Category Share`
26. `Price Avg`
27. `Price Median`

**Batch F — time intelligence**
28. `Sales Value Previous Year`
29. `Sales Value YoY %`
30. `Units Previous Year`
31. `Units YoY %`
32. `Sales Value MTD`
33. `Sales Value YTD`

After Batch A, drop a temporary Card with `Total Sales Value` to confirm the model works before continuing.

---

## Step 7 — Page A: Executive

1. Rename `Page 1` to **Executive**.
2. Add slicer: `dim_date[year]` (top left).
3. Add **4 Cards** across the top:
   - `[Total Units]`
   - `[Total Sales Value]`
   - `[Sales Value YoY %]`
   - `[Avg Daily Sales Value]`
4. Add **Line chart** (middle, wide):
   - X-axis: `agg_demand_trends[date]`
   - Y-axis: `[Daily Units]`, `[Rolling 7D Units]`
5. Add **Clustered bar** (bottom left):
   - Y-axis: `dim_store[store_id]`
   - X-axis: `[Total Sales Value]`
6. Add **Clustered column** (bottom right):
   - X-axis: `agg_daily_category_sales[cat_id]`
   - Y-axis: `[Category Sales Value]`
7. Resize so cards are one row, trend is full width, two charts share the bottom.

---

## Step 8 — Page B: Store Performance

1. **New page** → rename **Store**.
2. Slicers: `dim_store[state_id]`, `dim_date[year]`.
3. Cards: `[Total Sales Value]`, `[Total Units]`.
4. **Donut**: Legend `dim_store[state_id]` · Values `[Total Sales Value]`.
5. **Clustered bar**: Axis `dim_store[store_id]` · Values `[Total Sales Value]` → sort descending.
6. **Line chart**: X `agg_daily_store_sales[date]` · Legend `store_id` · Values `units_sold`.
7. **Matrix**: Rows `store_id` · Columns `agg_store_category_sales[cat_id]` · Values `[Category Share]` (% format).
8. **Table**: `store_id`, `state_id`, `[Total Units]`, `[Total Sales Value]`, `[Avg Sell Price]`.

---

## Step 9 — Page C: Product Analysis

1. **New page** → rename **Product**.
2. Slicers: `dim_product[cat_id]`, `dim_product[dept_id]`.
3. Cards: `[Product Units]`, `[Product Sales Value]`, `[Product Demand Volatility]`.
4. **Clustered bar** (Top 15):
   - Axis: `agg_product_performance[item_id]`
   - Values: `[Product Units]`
   - Filters pane on this visual: `units_rank` ≤ **15**  
     (or Top N filter on `item_id` by `[Product Units]` = 15)
5. **Clustered column**: X `cat_id` · Y `[Product Sales Value]`.
6. **Scatter**:
   - X: `avg_daily_units`
   - Y: `demand_volatility`
   - Size: `sales_value`
   - Legend: `cat_id`
7. **Table** from `agg_price_analysis`:
   - `cat_id`, `dept_id`, `avg_sell_price`, `median_sell_price`, `min_sell_price`, `max_sell_price`, `sales_value`

---

## Step 10 — Page D: Demand Planning

1. **New page** → rename **Demand**.
2. Slicers: `dim_date[year]`, `dim_date[month]`.
3. Cards: `[Daily Units]`, `[Rolling 7D Avg Units]`, `[Rolling 28D Units]`.
4. **Line chart**:
   - X: `agg_demand_trends[date]`
   - Y: `daily_units`, `rolling_7d_units`, `rolling_28d_units`
5. **Line and clustered column**:
   - X: `date`
   - Column: `[Daily Sales Value (Demand)]`
   - Line: `[Active SKUs (Demand)]`
6. **Clustered column**:
   - X: `agg_event_sales[event_label]`
   - Legend: `cat_id`
   - Y: `[Event Units]`
7. **Table**: `event_label`, `cat_id`, `days`, `units_sold`, `sales_value`, `avg_units_per_row`.

---

## Step 11 — Sync slicers + polish

1. Select the **year** slicer on Executive.
2. **View → Sync slicers**.
3. Sync `year` to Store / Product / Demand (as needed).
4. Format:
   - Sales measures → `$`
   - YoY / Category Share → `%`
   - Turn on title for each visual
5. **File → Save**.

---

## Step 12 — Quick validate

| Check | Expected |
|---|---|
| Executive cards show numbers | Non-blank after year filter |
| Store bar chart | 10 stores (CA/TX/WI) |
| Product Top 15 | Exactly 15 items |
| Demand line | Smooth curve with 7d/28d smoother than daily |
| YoY % | Blank or odd only if one year selected with no prior year |

Done when all 4 pages render without blank wrong relationships.
