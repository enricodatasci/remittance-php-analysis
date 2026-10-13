"""Timing analysis and dashboard exports.

Question: Does the day of the week, the time of the month, or the month of
the year change how many pesos $200 buys?

Method: Compare each day's exchange rate to its trailing 30-day average.
This removes the long-run trend (the peso weakening over years), so what
remains is the short-term timing effect.

Usage:
    python src/analysis.py
"""
import sqlite3
from pathlib import Path

import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "remittance.db"
DASH = ROOT / "dashboard"
TRANSFER_USD = 200

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def add_timing_features(fx: pd.DataFrame) -> pd.DataFrame:
    fx = fx.sort_values("rate_date").copy()
    fx["rolling_30d"] = fx["php_per_usd"].rolling(30, min_periods=20).mean()
    # Positive = this day's rate is better than usual (more pesos per dollar)
    fx["pct_vs_30d"] = 100 * (fx["php_per_usd"] / fx["rolling_30d"] - 1)
    fx["weekday"] = fx["rate_date"].dt.day_name()
    fx["month"] = fx["rate_date"].dt.month_name()
    fx["year"] = fx["rate_date"].dt.year
    fx["part_of_month"] = pd.cut(fx["rate_date"].dt.day, [0, 10, 20, 31],
                                 labels=["Early (1-10)", "Mid (11-20)", "Late (21-31)"])
    return fx.dropna(subset=["pct_vs_30d"])


def summarize(fx: pd.DataFrame, by: str, order: list) -> pd.DataFrame:
    """Average timing effect per group, plus what it means for $200."""
    out = (fx.groupby(by, observed=True)["pct_vs_30d"]
             .agg(avg_pct="mean", std="std", days="count")
             .reindex(order))
    avg_rate = fx["php_per_usd"].tail(250).mean()  # roughly the past year
    out["pesos_per_200_vs_avg"] = TRANSFER_USD * avg_rate * out["avg_pct"] / 100
    return out.round(3)


def anova_p(fx: pd.DataFrame, by: str) -> float:
    """One-way ANOVA: is there any real difference between the groups?"""
    groups = [g["pct_vs_30d"].values for _, g in fx.groupby(by, observed=True)]
    return stats.f_oneway(*groups).pvalue


def main() -> None:
    DASH.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        fx = pd.read_sql("SELECT * FROM fx_daily", conn, parse_dates=["rate_date"])
        ranks = pd.read_sql("SELECT * FROM v_provider_rank", conn)
        by_type = pd.read_sql("SELECT * FROM v_cost_by_type", conn)

    fx = add_timing_features(fx)
    weekday = summarize(fx, "weekday", WEEKDAYS)
    part = summarize(fx, "part_of_month", ["Early (1-10)", "Mid (11-20)", "Late (21-31)"])
    month = summarize(fx, "month", MONTHS)

    print("=== Timing effect: % vs trailing 30-day rate (positive = more pesos) ===")
    for name, table, col in [("Day of week", weekday, "weekday"),
                             ("Part of month", part, "part_of_month"),
                             ("Month", month, "month")]:
        p = anova_p(fx, col)
        verdict = "real difference" if p < 0.05 else "no real difference"
        print(f"\n{name}  (ANOVA p = {p:.3f}: {verdict})")
        print(table.to_string())

    # Compare timing to provider choice
    timing_range = month["pesos_per_200_vs_avg"].max() - month["pesos_per_200_vs_avg"].min()
    latest = ranks[ranks["quarter_start"] == ranks["quarter_start"].max()]
    mainstream = latest[latest["total_cost_pct"] < 10]  # exclude flat-fee outliers
    provider_range = mainstream["pesos_received"].max() - mainstream["pesos_received"].min()
    print(f"\nBest vs worst month:              about {timing_range:,.0f} pesos per $200")
    print(f"Best vs worst mainstream provider: about {provider_range:,.0f} pesos per $200")

    # Exports for Tableau
    fx[["rate_date", "php_per_usd", "rolling_30d", "pct_vs_30d", "weekday",
        "month", "year", "part_of_month"]].to_csv(DASH / "fx_daily.csv", index=False)
    ranks.to_csv(DASH / "provider_quarterly.csv", index=False)
    by_type.to_csv(DASH / "cost_by_provider_type.csv", index=False)
    (fx.pivot_table(index="month", columns="weekday", values="pct_vs_30d", aggfunc="mean")
       .reindex(index=MONTHS, columns=WEEKDAYS).round(3)
       .to_csv(DASH / "timing_heatmap.csv"))
    print(f"\nDashboard files saved to {DASH.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()