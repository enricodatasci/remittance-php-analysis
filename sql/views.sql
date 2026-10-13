-- Analytical views. Built after the tables are loaded.

-- 1. Average market exchange rate for each quarter
DROP VIEW IF EXISTS v_fx_quarterly;
CREATE VIEW v_fx_quarterly AS
SELECT
    DATE(rate_date, 'start of month',
         '-' || ((CAST(strftime('%m', rate_date) AS INTEGER) - 1) % 3) || ' months')
                         AS quarter_start,
    AVG(php_per_usd)     AS avg_php_per_usd,
    MIN(php_per_usd)     AS min_php_per_usd,
    MAX(php_per_usd)     AS max_php_per_usd,
    COUNT(*)             AS trading_days
FROM fx_daily
GROUP BY 1;

-- 2. Headline metric: pesos received per $200, one row per provider per quarter.
--    A provider can have several quotes per quarter (cash pickup, bank deposit,
--    etc.), so we keep both its average and its cheapest option.
DROP VIEW IF EXISTS v_pesos_per_200;
CREATE VIEW v_pesos_per_200 AS
SELECT
    p.quarter_start,
    p.provider,
    p.provider_type,
    COUNT(*)                                        AS quotes,
    AVG(p.fee_pct)                                  AS fee_pct,
    AVG(p.fx_margin_pct)                            AS fx_margin_pct,
    AVG(p.total_cost_pct)                           AS total_cost_pct,
    MIN(p.total_cost_pct)                           AS cheapest_cost_pct,
    MIN(p.transparent)                              AS fully_transparent,
    f.avg_php_per_usd,
    200 * f.avg_php_per_usd                                   AS pesos_if_free,
    200 * (1 - AVG(p.total_cost_pct) / 100) * f.avg_php_per_usd AS pesos_received,
    200 * (1 - MIN(p.total_cost_pct) / 100) * f.avg_php_per_usd AS pesos_received_best_option,
    200 * (AVG(p.total_cost_pct) / 100) * f.avg_php_per_usd     AS pesos_lost_to_costs
FROM provider_costs p
JOIN v_fx_quarterly f ON f.quarter_start = p.quarter_start
GROUP BY p.quarter_start, p.provider, p.provider_type;

-- 3. Rank providers within each quarter (1 = most pesos delivered)
DROP VIEW IF EXISTS v_provider_rank;
CREATE VIEW v_provider_rank AS
SELECT
    *,
    RANK() OVER (PARTITION BY quarter_start ORDER BY pesos_received DESC) AS rank_in_quarter,
    COUNT(*) OVER (PARTITION BY quarter_start)                            AS providers_in_quarter,
    pesos_received - MAX(pesos_received) OVER (PARTITION BY quarter_start) AS pesos_vs_best,
    pesos_received - LAG(pesos_received) OVER (PARTITION BY provider ORDER BY quarter_start)
                                                                           AS change_vs_prior_qtr
FROM v_pesos_per_200;

-- 4. Cost by provider type over time
DROP VIEW IF EXISTS v_cost_by_type;
CREATE VIEW v_cost_by_type AS
SELECT
    quarter_start,
    provider_type,
    COUNT(DISTINCT provider) AS providers,
    AVG(total_cost_pct)      AS avg_total_cost_pct,
    AVG(pesos_received)      AS avg_pesos_received
FROM v_pesos_per_200
GROUP BY quarter_start, provider_type;