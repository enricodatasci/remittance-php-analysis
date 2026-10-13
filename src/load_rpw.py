"""Clean the World Bank Remittance Prices Worldwide (RPW) dataset.

Reads both data sheets (the format changed in Q2 2016), keeps only the
United States to Philippines corridor, and saves one tidy CSV.

Download: https://remittanceprices.worldbank.org/data-download
Save as:  data/raw/rpw_dataset.xlsx

Usage:
    python src/load_rpw.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "rpw_dataset.xlsx"
OUT_FILE = ROOT / "data" / "processed" / "provider_costs.csv"

SHEETS = ["Dataset (up to Q1 2016)", "Dataset (from Q2 2016)"]

# Raw column name -> clean column name
COLUMNS = {
    "period": "period",
    "date": "survey_date",
    "firm": "provider",
    "firm_type": "provider_type",
    "speed actual": "speed",
    "pickup method": "pickup_method",
    "cc1 lcu amount": "amount_usd",
    "cc1 lcu fee": "fee_usd",
    "cc1 fx margin": "fx_margin_pct",
    "cc1 total cost %": "total_cost_pct",
    "transparent": "transparent",
}

# Same company under different names in different years
PROVIDER_ALIASES = {
    "Transferwise": "Wise",
    "TransferWise": "Wise",
    "Trans-Fast": "Transfast",
}

def read_sheet(sheet: str) -> pd.DataFrame:
    df = pd.read_excel(RAW_FILE, sheet_name=sheet)
    # The old sheet spells it "pick-up method", the new one "pickup method"
    df = df.rename(columns={"pick-up method": "pickup method"})
    # Keep only money sent from the U.S. to the Philippines
    df = df[(df["source_code"] == "USA") & (df["destination_code"] == "PHL")]
    return df[list(COLUMNS)].rename(columns=COLUMNS)


def period_to_quarter(period: str) -> pd.Timestamp:
    """Turn '2024_1Q' into the first day of that quarter (2024-01-01)."""
    year, q = str(period).split("_")
    return pd.Timestamp(year=int(year), month=3 * int(q[0]) - 2, day=1)


def main() -> None:
    df = pd.concat([read_sheet(s) for s in SHEETS], ignore_index=True)

    # The World Bank uses ".." for missing values
    df = df.replace("..", pd.NA)

    df["quarter_start"] = df["period"].map(period_to_quarter)
    df["survey_date"] = pd.to_datetime(df["survey_date"], format="%d/%b/%Y", errors="coerce")
    for col in ["amount_usd", "fee_usd", "fx_margin_pct", "total_cost_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fee as a % of the $200 sent, so it can be compared with the FX margin
    df["fee_pct"] = 100 * df["fee_usd"] / df["amount_usd"]

    # "no" means the provider didn't disclose its exchange rate, so its
    # fx_margin_pct of 0 is unknown, not free. Flag it for the analysis.
    df["transparent"] = df["transparent"].astype(str).str.strip().str.lower() == "yes"
    df["provider"] = df["provider"].astype(str).str.strip()
    df["provider"] = df["provider"].replace(PROVIDER_ALIASES)

    df = df.dropna(subset=["total_cost_pct"]).sort_values(["quarter_start", "provider"])

    cols = ["quarter_start", "period", "survey_date", "provider", "provider_type",
            "speed", "pickup_method", "amount_usd", "fee_usd", "fee_pct",
            "fx_margin_pct", "total_cost_pct", "transparent"]
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df[cols].to_csv(OUT_FILE, index=False)

    print(f"Saved {len(df):,} U.S. to Philippines price quotes")
    print(f"Quarters: {df.period.iloc[0]} to {df.period.iloc[-1]} "
          f"({df.quarter_start.nunique()} total)")
    print(f"Providers: {df.provider.nunique()}  |  "
          f"Not transparent: {(~df.transparent).sum()} quotes")
    print("\nAverage total cost by provider type:")
    print(df.groupby("provider_type")["total_cost_pct"].mean().round(2).to_string())


if __name__ == "__main__":
    main()