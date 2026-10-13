"""Load the processed CSVs into a SQLite database and build the analysis views.

Usage:
    python src/build_db.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
DB_PATH = PROCESSED / "remittance.db"


def main() -> None:
    fx = pd.read_csv(PROCESSED / "fx_daily.csv")
    costs = pd.read_csv(PROCESSED / "provider_costs.csv")
    costs["transparent"] = costs["transparent"].astype(int)

    with sqlite3.connect(DB_PATH) as conn:
        # 1. Create empty tables
        conn.executescript((SQL_DIR / "schema.sql").read_text())
        # 2. Fill them with the CSV data
        fx.to_sql("fx_daily", conn, if_exists="append", index=False)
        costs.to_sql("provider_costs", conn, if_exists="append", index=False)
        # 3. Build the analysis views on top
        conn.executescript((SQL_DIR / "views.sql").read_text())

        n_fx = conn.execute("SELECT COUNT(*) FROM fx_daily").fetchone()[0]
        n_costs = conn.execute("SELECT COUNT(*) FROM provider_costs").fetchone()[0]
        n_joined = conn.execute("SELECT COUNT(*) FROM v_pesos_per_200").fetchone()[0]
        missing = conn.execute("""
            SELECT COUNT(DISTINCT quarter_start) FROM provider_costs
            WHERE quarter_start NOT IN (SELECT quarter_start FROM v_fx_quarterly)
        """).fetchone()[0]

    print(f"Built {DB_PATH.relative_to(ROOT)}")
    print(f"  fx_daily:        {n_fx:,} rows")
    print(f"  provider_costs:  {n_costs:,} rows")
    print(f"  v_pesos_per_200: {n_joined:,} provider-quarter rows")
    if missing:
        print(f"  WARNING: {missing} quarters have no exchange rate data. "
              "Re-run fetch_fx.py with an earlier --start date.")


if __name__ == "__main__":
    main()