"""Validate Power BI Executive (Dashboard 1) KPIs against data/gold_export."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold_export"


def main() -> None:
    store = pd.read_parquet(GOLD / "agg_daily_store_sales.parquet")
    cat = pd.read_parquet(GOLD / "agg_daily_category_sales.parquet")
    demand = pd.read_parquet(GOLD / "agg_demand_trends.parquet")
    dim_date = pd.read_parquet(GOLD / "dim_date.parquet")

    store["date"] = pd.to_datetime(store["date"])
    cat["date"] = pd.to_datetime(cat["date"])
    demand["date"] = pd.to_datetime(demand["date"])
    dim_date["date"] = pd.to_datetime(dim_date["date"])

    total_units = int(store["units_sold"].sum())
    total_sales = float(store["sales_value"].sum())
    n_days = int(store["date"].nunique())
    avg_daily_sales = total_sales / n_days

    sales_by_day = store.groupby("date")["sales_value"].sum()
    prev = 0.0
    for d in dim_date["date"]:
        ly = d - pd.DateOffset(years=1)
        if ly in sales_by_day.index:
            prev += float(sales_by_day.loc[ly])
    yoy = (total_sales - prev) / prev if prev else float("nan")

    store_rank = (
        store.groupby("store_id")["sales_value"].sum().sort_values(ascending=False)
    )
    cat_rank = (
        cat.groupby("cat_id")["sales_value"].sum().sort_values(ascending=False)
    )
    days_by_year = demand.groupby(demand["date"].dt.year).size()
    avg_units_by_year = demand.groupby(demand["date"].dt.year)["daily_units"].mean()
    sales_by_year = store.groupby(store["date"].dt.year)["sales_value"].sum()

    print("=== Executive KPI validation (gold_export) ===")
    print(f"Total Units:            {total_units:,}  (dashboard ~67M)")
    print(f"Total Sales Value:      ${total_sales:,.2f}  (dashboard $191.577…M)")
    print(f"Avg Daily Sales Value:  ${avg_daily_sales:,.2f}  (dashboard 98.70K)")
    print(f"Sales Value YoY %:      {yoy*100:.2f}%  (dashboard ~27.08%; DAX SAMEPERIODLASTYEAR)")
    print(f"Sales window:           {store['date'].min().date()} → {store['date'].max().date()} ({n_days} days)")
    print(f"dim_date window:        {dim_date['date'].min().date()} → {dim_date['date'].max().date()} ({len(dim_date)} days)")
    print()
    print("Days / avg daily units by year:")
    for y in sorted(days_by_year.index):
        print(
            f"  {y}: {int(days_by_year[y]):3d} days | "
            f"avg daily units {avg_units_by_year[y]:,.0f} | "
            f"sales ${sales_by_year[y]:,.0f}"
        )
    print()
    print("Store ranking (sales_value):")
    for sid, val in store_rank.items():
        print(f"  {sid}: ${val:,.2f}")
    print()
    print("Category mix:")
    for cid, val in cat_rank.items():
        print(f"  {cid}: ${val:,.2f} ({val/total_sales*100:.1f}%)")
    print()
    print("Key pattern: 2016 has only", int(days_by_year[2016]), "days but highest avg daily units.")
    print(
        "Key pattern: CA_3 is #1 at "
        f"${store_rank.iloc[0]:,.0f} (~{store_rank.iloc[0]/total_sales*100:.1f}% of sales); "
        f"CA_4 last; ratio CA_3/CA_4 = {store_rank.iloc[0]/store_rank.iloc[-1]:.2f}x"
    )
    print(
        "Key pattern: FOODS dominates at "
        f"{cat_rank.iloc[0]/total_sales*100:.1f}% of sales value."
    )


if __name__ == "__main__":
    main()
