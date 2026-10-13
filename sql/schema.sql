-- Tables for the remittance analysis (SQLite)

DROP TABLE IF EXISTS fx_daily;
CREATE TABLE fx_daily (
    rate_date      DATE PRIMARY KEY,
    php_per_usd    REAL NOT NULL,
    pesos_per_200  REAL,
    source         TEXT
);

DROP TABLE IF EXISTS provider_costs;
CREATE TABLE provider_costs (
    quarter_start   DATE NOT NULL,
    period          TEXT,
    survey_date     DATE,
    provider        TEXT NOT NULL,
    provider_type   TEXT,
    speed           TEXT,
    pickup_method   TEXT,
    amount_usd      REAL,
    fee_usd         REAL,
    fee_pct         REAL,     -- fee as % of amount sent
    fx_margin_pct   REAL,     -- exchange rate markup vs. market rate, %
    total_cost_pct  REAL NOT NULL,
    transparent     INTEGER   -- 1 = provider disclosed its exchange rate
);

CREATE INDEX idx_provider_quarter ON provider_costs (provider, quarter_start);