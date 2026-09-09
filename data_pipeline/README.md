# Module 1 — Data Pipeline

## Overview
Automated data pipeline for catalog extraction, normalization, and relational querying.
Data source: `books.toscrape.com`

## Acceptance Results (from latest run)
- Scraped: 69 books across 3 categories (Travel, Mystery, Historical Fiction) — meets criteria (>= 60 books, >= 3 categories)
- Rows dropped due to unparseable price: 0
- Rows requiring median rating imputation: 0 (computed median = 3)
- SQL/pandas JOIN verification: Exact Data Match Confirmed = True

## Pipeline Decisions & Acceptance Verification
1. **Polite Scraping**: Implemented `time.sleep(0.2)` rate-limiting delay between page requests, wrapped in per-item `try-except` blocks.
2. **Dynamic Median Imputation**: Parsed valid numeric star ratings and dynamically computed the empirical median rating (median = 3).
3. **Currency Conversion Baseline**: Enforced fixed baseline conversion `1 GBP = 105.50 INR` for `price_inr`. Corrupted numeric rows are safely dropped.
4. **Relational Schema**:
   - `categories(category_id INTEGER PRIMARY KEY, category_name TEXT UNIQUE)`
   - `books(book_id INTEGER PRIMARY KEY, title TEXT, price_gbp REAL, price_inr REAL, rating INTEGER, in_stock INTEGER, category_id REFERENCES categories(category_id))`
5. **SQL & Pandas Equivalence**: Verified Query 5 INNER JOIN against in-memory `pandas.merge()`; both row sets and ordering matched identically (`Exact Data Match Confirmed: True`).

## Run Pipeline
```bash
python data_pipeline/scraper.py
```