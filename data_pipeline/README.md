# Module 1 — Data Pipeline

## Overview
Automated data pipeline responsible for scraping catalog pricing and availability, cleaning and normalizing data fields, enforcing relational SQLite storage, and executing SQL and pandas analytics.

- **Target Source**: `books.toscrape.com`
- **Output Database**: `books_catalogue.db`
- **Output Query Log**: `query_outputs.txt`

---

## Acceptance Verification Results
- **Items Ingested**: 69 books across 3 categories (`Travel`, `Mystery`, `Historical Fiction`). Meets requirement (>= 60 books, >= 3 categories).
- **Corrupted Price Rows Dropped**: 0
- **Missing Ratings Imputed**: 0 (Computed empirical median rating = 3).
- **Column Dtypes**: `price_gbp` (float64), `price_inr` (float64), `rating` (int64), `in_stock` (bool).
- **SQL / Pandas Equivalence**: Verified Query 5 (INNER JOIN) against in-memory `pd.merge()`. Exact Data Match Confirmed: `True`.

---

## Pipeline Decisions & Data Transformations
1. **Polite Scraping & Element Resilience**:
   - Enforced a `time.sleep(0.2)` rate-limiting delay between page requests.
   - Wrapped individual book parsing inside `try-except` blocks to prevent page traversal crashes on malformed HTML elements.
2. **Fixed Baseline Currency Conversion**:
   - Converted `price_gbp` to `price_inr` using the constant baseline: **1 GBP = 105.50 INR**.
   - No external currency API was utilized, maintaining deterministic and reproducible offline evaluation.
3. **Data Cleaning & Missing Value Handling**:
   - Stripped currency characters (`£`) and parsed prices into floats.
   - Converted text ratings (`One` to `Five`) to integers (`1` to `5`).
   - If an unparseable numeric rating is encountered, it is imputed with the empirical dataset median.
   - Converted availability status into native boolean values (`in_stock: bool`).
4. **Relational Schema**:
   - `categories(category_id INTEGER PRIMARY KEY AUTOINCREMENT, category_name TEXT UNIQUE)`
   - `books(book_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price_gbp REAL, price_inr REAL, rating INTEGER, in_stock INTEGER, category_id REFERENCES categories(category_id))`
   - Enforced foreign keys using `PRAGMA foreign_keys = ON;`.
5. **Saved Queries & Equivalence**:
   - Executed 5 queries covering `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, `DISTINCT`, `BETWEEN`, and `JOIN`.
   - Read results via `pd.read_sql(...)`.
   - Saved all SQL queries and output tables to `query_outputs.txt`.
   - Side-by-side verification confirms identical row ordering and content between SQL and `pd.merge()`.

---

## Installation & Execution

```bash
# Run data pipeline
python data_pipeline/scraper.py
```