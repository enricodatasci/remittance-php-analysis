"""2026 spot check: compare today's quotes for sending $200 USD to PHP.

Reads data/raw/spot_check_2026.csv (quotes collected by hand) and splits
each provider's cost into the visible fee and the hidden exchange rate
markup, measured against the mid-market rate.

Note: "total_fees_usd" is the all-in cost as shown on Wise's comparison
page, which includes both the transfer fee and the exchange rate markup.

Usage:
    python src/spot_check.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "spot_check_2026.csv"
OUT = ROOT / "data" / "processed" / "spot_check_2026.csv"

# Wise converts at the mid-market rate, so its quoted rate is the benchmark
MID_MARKET_SOURCE = "Wise"


def main() -> None:
    df = pd.read_csv(RAW)
    mid = df.loc[df["provider"] == MID_MARKET_SOURCE, "provider_rate"].iloc[0]

    df["mid_market_rate"] = mid
    df["total_cost_pct"] = 100 * df["total_fees_usd"] / df["send_usd"]
    df["fx_margin_pct"] = 100 * (1 - df["provider_rate"] / mid)
    df["fee_pct"] = (df["total_cost_pct"] - df["fx_margin_pct"]).clip(lower=0)
    df["php_if_free"] = df["send_usd"] * mid
    df = df.sort_values("php_received", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    cols = ["rank", "provider", "php_received", "fee_pct", "fx_margin_pct", "total_cost_pct"]
    print(f"Spot check {df.collected_date.iloc[0]}: $200 to PHP (mid-market {mid})")
    print(df[cols].round(2).to_string(index=False))
    gap = df.php_received.max() - df.php_received.min()
    print(f"\nBest vs worst: {gap:,.0f} PHP per transfer, {12 * gap:,.0f} PHP per year")


if __name__ == "__main__":
    main()