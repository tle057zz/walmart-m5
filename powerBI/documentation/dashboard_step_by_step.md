# Power BI — Dashboard build (visual by visual)

Do this **after** relationships + all 33 measures are in `_Measures`.

Save often: `powerbi/walmart_m5_gold.pbix`

---

# PAGE 1 — Executive

## 1.1 Rename the page
1. Bottom tab: double-click `Page 1`
2. Type: `Executive`
3. Enter

## 1.2 Year slicer
1. Click empty canvas
2. Visualizations → **Slicer**
3. Fields → expand `dim_date` → check `year`
4. Place top-left
5. Optional: Format → Slicer settings → Style → **Dropdown**

## 1.3 Card — Total Units
1. Click empty canvas → **Card**
2. Fields → `_Measures` → check **Total Units**
3. Place top row, left
4. Format → Callout value → Display units → **Auto** or **None**

## 1.4 Card — Total Sales Value
1. New **Card**
2. Field: **Total Sales Value**
3. Place next to Total Units
4. Format as Currency if not already (`$`)

## 1.5 Card — Sales Value YoY %
1. New **Card**
2. Field: **Sales Value YoY %**
3. Place next
4. Format as **Percentage** (1 decimal)

## 1.6 Card — Avg Daily Sales Value
1. New **Card**
2. Field: **Avg Daily Sales Value**
3. Place next (4 cards in one row)

## 1.7 Line chart — Demand trend
1. New **Line chart**
2. X-axis: `agg_demand_trends` → `date`
3. Y-axis: `_Measures` → **Daily Units**
4. Y-axis again: `_Measures` → **Rolling 7D Units**
5. Stretch full width under the cards
6. Format → Title → On → text: `Demand trend (daily vs 7-day)`

## 1.8 Clustered bar — Store ranking
1. New **Clustered bar chart**
2. Y-axis: `dim_store` → `store_id`
3. X-axis: **Total Sales Value**
4. Place bottom-left
5. Click chart → More options (…) → **Sort by Total Sales Value** → **Sort descending**
6. Title: `Sales by store`

## 1.9 Clustered column — Category
1. New **Clustered column chart**
2. X-axis: `agg_daily_category_sales` → `cat_id`
3. Y-axis: **Category Sales Value**
4. Place bottom-right
5. Title: `Sales by category`

## 1.10 Check
- Pick a year in the slicer → all visuals should update
- Cards should not be blank
- Store chart shows ~10 stores

---

# PAGE 2 — Store

## 2.1 New page
1. Bottom → **+** new page
2. Rename to `Store`

## 2.2 Slicers
1. **Slicer** → `dim_store` → `state_id` (top-left)
2. **Slicer** → `dim_date` → `year` (next to it)

## 2.3 Cards
1. **Card** → **Total Sales Value**
2. **Card** → **Total Units**

## 2.4 Donut — Sales by state
1. New **Donut chart**
2. Legend: `dim_store` → `state_id`
3. Values: **Total Sales Value**
4. Title: `Sales by state`

## 2.5 Clustered bar — Store ranking
1. New **Clustered bar chart**
2. Y-axis: `dim_store` → `store_id`
3. X-axis: **Total Sales Value**
4. Sort descending by Total Sales Value
5. Title: `Store ranking`

## 2.6 Line chart — Daily units by store
1. New **Line chart**
2. X-axis: `agg_daily_store_sales` → `date`
3. Legend: `agg_daily_store_sales` → `store_id`
4. Y-axis: `agg_daily_store_sales` → `units_sold`  
   (or use **Total Units** if it filters correctly)
5. Title: `Daily units by store`
6. Tip: with many stores, filter visual to 1–3 stores via Filters pane if crowded

## 2.7 Matrix — Category share
1. New **Matrix**
2. Rows: `agg_store_category_sales` → `store_id`
3. Columns: `agg_store_category_sales` → `cat_id`
4. Values: **Category Share**
5. Select the measure in Values → Format as **%**
6. Title: `Category share by store`

## 2.8 Table — Store summary
1. New **Table**
2. Add columns/measures in order:
   - `dim_store` → `store_id`
   - `dim_store` → `state_id`
   - **Total Units**
   - **Total Sales Value**
   - **Avg Sell Price**
3. Title: `Store summary`

## 2.9 Check
- Click `CA` in state slicer → only CA stores remain
- Matrix shows FOODS / HOBBIES / HOUSEHOLD shares

---

# PAGE 3 — Product

## 3.1 New page
1. **+** → rename `Product`

## 3.2 Slicers
1. **Slicer** → `dim_product` → `cat_id`
2. **Slicer** → `dim_product` → `dept_id`

## 3.3 Cards
1. **Card** → **Product Units**
2. **Card** → **Product Sales Value**
3. **Card** → **Product Demand Volatility**

## 3.4 Clustered bar — Top 15 products
1. New **Clustered bar chart**
2. Y-axis: `agg_product_performance` → `item_id`
3. X-axis: **Product Units**
4. Open **Filters** pane (right) → under **Filters on this visual**:
   - Drag `agg_product_performance` → `units_rank` into Filters on this visual
   - Filter type: **is less than or equal to**
   - Value: `15`
   - Apply filter
5. Sort by Product Units descending
6. Title: `Top 15 products by units`

Alternative if `units_rank` filter fails:
- Filters on this visual → `item_id` → **Filter type: Top N**
- Show items: Top `15`
- By value: **Product Units**

## 3.5 Clustered column — Sales by category
1. New **Clustered column chart**
2. X-axis: `agg_product_performance` → `cat_id`
3. Y-axis: **Product Sales Value**
4. Title: `Product sales by category`

## 3.6 Scatter — Volatility vs volume
1. New **Scatter chart**
2. X-axis: `agg_product_performance` → `avg_daily_units`
3. Y-axis: `agg_product_performance` → `demand_volatility`
4. Size: `agg_product_performance` → `sales_value`
5. Legend: `agg_product_performance` → `cat_id`
6. Title: `Volatility vs avg daily units`

## 3.7 Table — Price analysis
1. New **Table**
2. From `agg_price_analysis`, add:
   - `cat_id`
   - `dept_id`
   - `avg_sell_price`
   - `median_sell_price`
   - `min_sell_price`
   - `max_sell_price`
   - `sales_value`
3. Title: `Price analysis by dept`

## 3.8 Check
- Top bar shows exactly 15 items
- Scatter has 3 category colors
- Price table has FOODS / HOBBIES / HOUSEHOLD depts

---

# PAGE 4 — Demand

## 4.1 New page
1. **+** → rename `Demand`

## 4.2 Slicers
1. **Slicer** → `dim_date` → `year`
2. **Slicer** → `dim_date` → `month`

## 4.3 Cards
1. **Card** → **Daily Units**
2. **Card** → **Rolling 7D Avg Units**
3. **Card** → **Rolling 28D Units**

## 4.4 Line chart — Rolling demand
1. New **Line chart**
2. X-axis: `agg_demand_trends` → `date`
3. Y-axis add all three:
   - `agg_demand_trends` → `daily_units`  
     **or** measure **Daily Units**
   - `agg_demand_trends` → `rolling_7d_units`  
     **or** **Rolling 7D Units**
   - `agg_demand_trends` → `rolling_28d_units`  
     **or** **Rolling 28D Units**
4. Title: `Daily vs rolling 7 / 28 day demand`
5. Stretch wide under cards

## 4.5 Line and clustered column — Sales + active SKUs
1. New **Line and clustered column chart**
2. X-axis: `agg_demand_trends` → `date`
3. Column y-axis: **Daily Sales Value (Demand)**
4. Line y-axis: **Active SKUs (Demand)**
5. Title: `Sales value vs active SKUs`

## 4.6 Clustered column — Event impact
1. New **Clustered column chart**
2. X-axis: `agg_event_sales` → `event_label`
3. Legend: `agg_event_sales` → `cat_id`
4. Y-axis: **Event Units**
5. Title: `Units by event type and category`

## 4.7 Table — Event detail
1. New **Table**
2. From `agg_event_sales`:
   - `event_label`
   - `cat_id`
   - `days`
   - `units_sold`
   - `sales_value`
   - `avg_units_per_row`
3. Title: `Event sales detail`

## 4.8 Check
- Rolling lines look smoother than daily
- Event chart has labels like event / no-event (or your `event_label` values)
- Month slicer narrows the demand line

---

# FINAL — Sync + polish

## 5.1 Sync year slicer
1. Go to **Executive**
2. Click the **year** slicer
3. Ribbon → **View** → check **Sync slicers**
4. In Sync slicers pane:
   - Sync column: tick Store, Product, Demand (as needed)
   - Visible column: tick where you want it shown

## 5.2 Titles + layout
1. Align cards in one row on each page
2. Keep one main chart wide
3. Turn **Title** on for every visual

## 5.3 Number formats (if missing)
| Measure | Format |
|---|---|
| Total Sales Value, Category Sales Value, Product Sales Value, Daily Sales Value (Demand), Event Sales Value, Avg Daily Sales Value, Sales Value MTD/YTD | Currency `$` |
| Sales Value YoY %, Units YoY %, Category Share | Percentage `0.0%` |

## 5.4 Save
**File → Save** → `walmart_m5_gold.pbix`

---

# Done checklist

- [ ] Executive: 4 cards + demand line + store bar + category column
- [ ] Store: state donut + store bar + daily line + share matrix + table
- [ ] Product: 3 cards + top 15 + category column + scatter + price table
- [ ] Demand: 3 cards + rolling line + combo chart + event column + event table
- [ ] Year slicer synced
- [ ] File saved
