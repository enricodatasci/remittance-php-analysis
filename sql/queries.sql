-- Business questions answered with SQL.
-- Run with: python src/run_queries.py

-- Q1. Provider ranking in the most recent quarter
SELECT rank_in_quarter                  AS rank,
       provider,
       provider_type,
       ROUND(total_cost_pct, 2)         AS total_cost_pct,
       ROUND(pesos_received, 0)         AS pesos_received,
       ROUND(pesos_vs_best, 0)          AS pesos_vs_best
FROM v_provider_rank
WHERE quarter_start = (SELECT MAX(quarter_start) FROM v_provider_rank)
ORDER BY rank_in_quarter;

-- Q2. Hidden costs: providers whose exchange rate markup is bigger than their fee
SELECT provider,
       ROUND(AVG(fee_pct), 2)        AS avg_fee_pct,
       ROUND(AVG(fx_margin_pct), 2)  AS avg_fx_margin_pct,
       ROUND(AVG(fx_margin_pct) / AVG(total_cost_pct) * 100, 0) AS pct_of_cost_hidden
FROM v_pesos_per_200
GROUP BY provider
HAVING AVG(fx_margin_pct) > AVG(fee_pct)
ORDER BY avg_fx_margin_pct DESC;

-- Q3. Most reliable providers: how often each finished in the top 3
SELECT provider,
       COUNT(*)                                               AS quarters_surveyed,
       SUM(rank_in_quarter <= 3)                              AS top3_finishes,
       ROUND(100.0 * SUM(rank_in_quarter <= 3) / COUNT(*), 1) AS top3_rate_pct
FROM v_provider_rank
GROUP BY provider
HAVING COUNT(*) >= 8
ORDER BY top3_rate_pct DESC;

-- Q4. Cost of picking the worst provider instead of the best, $200 sent monthly
SELECT quarter_start,
       ROUND(MAX(pesos_received) - MIN(pesos_received), 0)        AS gap_per_transfer,
       ROUND(12 * (MAX(pesos_received) - MIN(pesos_received)), 0) AS gap_per_year
FROM v_pesos_per_200
GROUP BY quarter_start
ORDER BY quarter_start DESC
LIMIT 8;

-- Q5. Corridor vs. the UN target of 3% total cost, by year
SELECT strftime('%Y', quarter_start)              AS year,
       ROUND(AVG(total_cost_pct), 2)              AS avg_cost_pct,
       SUM(total_cost_pct <= 3)                   AS provider_quarters_meeting_target,
       COUNT(*)                                   AS provider_quarters_total
FROM v_pesos_per_200
GROUP BY year
ORDER BY year;