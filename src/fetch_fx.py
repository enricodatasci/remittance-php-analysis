"""Pull daily USD/PHP mid-market exchange rates.

Source: Frankfurter API (European Central Bank reference rates, free, no key).

Usage:
    python src/fetch_fx.py --start 2015-01-01
"""
import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "processed"
API_URL = "https://api.frankfurter.dev/v1/{start}..{end}"


def fetch_daily_rates(start: str, end: str) -> pd.DataFrame:
    """Return a DataFrame with one row per trading day: PHP per 1 USD."""
    resp = requests.get(
        API_URL.format(start=start, end=end),
        params={"from": "USD", "to": "PHP"},
        timeout=60,
    )
    resp.raise_for_status()
    rates = resp.json()["rates"]  # {"2026-09-01": {"PHP": 62.43}, ...}

    df = pd.DataFrame(
        [{"rate_date": day, "php_per_usd": vals["PHP"]} for day, vals in rates.items()]
    )
    df["rate_date"] = pd.to_datetime(df["rate_date"])
    df["pesos_per_200"] = 200 * df["php_per_usd"]
    df["source"] = "ECB via Frankfurter"
    return df.sort_values("rate_date").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download USD/PHP exchange rates")
    parser.add_argument("--start", default="2015-01-01", help="YYYY-MM-DD")
    parser.add_argument("--end", default=date.today().isoformat(), help="YYYY-MM-DD")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = fetch_daily_rates(args.start, args.end)
    df.to_csv(OUT_DIR / "fx_daily.csv", index=False)

    print(f"Saved {len(df):,} daily rates "
          f"({df.rate_date.min():%Y-%m-%d} to {df.rate_date.max():%Y-%m-%d})")
    print(f"Latest: 1 USD = {df.php_per_usd.iloc[-1]:.2f} PHP, "
          f"so $200 = {df.pesos_per_200.iloc[-1]:,.0f} PHP before fees")


if __name__ == "__main__":
    main()