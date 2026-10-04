# Remittance Timing & Provider Cost Analysis (USD to PHP)

**An analytics project to help U.S. immigrant families understand where their money goes when sending it home to the Philippines.**

## Why This Project

My family regularly sends money to relatives in the Philippines. Like many families, they usually pick a provider out of habit or convenience, without knowing how much is lost to fees and exchange rate markups. A provider advertising "no fees" can still deliver fewer pesos than one that charges a visible fee, because the real cost is hidden in the exchange rate.

This project turns that into a data question and gives families a simple, clear answer.

## Business Questions

1. **Which provider delivers the most pesos per $200 sent**, after all fees and exchange rate markups?
2. **How much is hidden?** How much of each provider's cost is the visible fee vs. the exchange rate margin?
3. **Banks vs. digital providers:** Is one type consistently cheaper?
4. **Does timing matter?** Does the day of the week or month change how many pesos arrive?
5. **What's it worth?** How many pesos per year does a family save by switching from the worst provider to the best?

## Key Metric

**Pesos received per $200 sent**

```
pesos_received = 200 × (1 − total_cost_% / 100) × mid_market_exchange_rate
```

`total_cost_%` combines the transfer fee and the exchange rate margin, so every provider is compared on what the family actually receives.

## Data Sources

| Source | What it provides |
|---|---|
| [Frankfurter API](https://frankfurter.dev/) (European Central Bank rates) | Daily USD/PHP mid-market exchange rate |
| [FRED](https://fred.stlouisfed.org/series/FXRATEPHA618NUPN) | Long-run annual PHP per USD exchange rate |
| [Bangko Sentral ng Pilipinas](https://www.bsp.gov.ph/statistics/external/day99_data.aspx) | Official Philippine peso reference rate |
| [World Bank Remittance Prices Worldwide](https://remittanceprices.worldbank.org/data-download) | Fees, exchange rate margins, and total cost by provider |

## Tools

- **Python** (pandas, requests): data collection, cleaning, analysis
- **SQL** (SQLite): data storage, provider rankings, cost comparisons
- **Tableau**: interactive dashboard
- **Excel**: "what if I send $X per month" savings calculator

## Project Structure

```
remittance-php-analysis/
├── data/
│   ├── raw/           # Source files (not committed)
│   └── processed/     # Cleaned data
├── src/               # Python scripts
├── sql/               # Database schema and analysis queries
├── dashboard/         # Tableau files and data extracts
├── reports/           # Findings and recommendations
└── README.md
```

## Project Status

- [x] Project setup
- [ ] Exchange rate data pipeline
- [ ] Provider cost data cleaning
- [ ] SQL database and analysis queries
- [ ] Timing analysis
- [ ] Tableau dashboard
- [ ] Findings and family guide

## Findings

*Coming soon.*

## Author

**Enrico Ong**, Statistical Data Science, University of Connecticut