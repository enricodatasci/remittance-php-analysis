"""Run every query in sql/queries.sql and print the results.

Usage:
    python src/run_queries.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "remittance.db"
QUERIES = ROOT / "sql" / "queries.sql"

pd.set_option("display.width", 120)


def main() -> None:
    # Split the file on semicolons; the comment above each query is its title
    blocks = [b.strip() for b in QUERIES.read_text().split(";") if "SELECT" in b]
    with sqlite3.connect(DB_PATH) as conn:
        for block in blocks:
            title = next(l for l in block.splitlines() if l.startswith("-- Q"))
            print(f"\n{title[3:]}")
            print(pd.read_sql(block, conn).to_string(index=False))


if __name__ == "__main__":
    main()