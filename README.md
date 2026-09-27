# Zepto Data & AI Platform — Capstone Project

A single connected platform: a data-engineering pipeline, an end-to-end analytics/ML pipeline, and a GenAI support assistant, all in one repository.

## Repository Structure

/data_pipeline      — Module 1: scrape → clean → convert → store → query (25 marks)
/analytics           — Module 2: EDA + predictive modeling on Titanic (50 marks)
/support_assistant   — Module 3: RAG-based GenAI support assistant (25 marks)


## Setup

One consolidated `requirements.txt` at the repository root covers all three
modules:
```bash
pip install -r requirements.txt
```

## Running Each Module

**Module 1 — Data Pipeline**
```bash
python data_pipeline/scraper.py
```
Outputs: `data_pipeline/books_catalogue.db`, `data_pipeline/query_outputs.txt`.
See `data_pipeline/README.md` for full design decisions.

**Module 2 — Analytics Pipeline**
Open and run, in order:
1. `analytics/01_eda.ipynb` — profiling, cleaning, EDA, saves `titanic.csv`
2. `analytics/02_modeling.ipynb` — full modeling pipeline, saves
   `analytics/models/best_titanic_pipeline.joblib`

See `analytics/README.md` for the full model comparison table and
recommendation.

**Module 3 — Support Assistant**
```bash
python support_assistant/ingest.py      # one-time: build the vector store
cd support_assistant
python -m uvicorn main:app --host 0.0.0.0 --port 7860
```
Or via Docker:
```bash
docker build -f support_assistant/Dockerfile -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```
See `support_assistant/README.md` for the architecture description and
example API calls.

## Design Decisions Summary

- **Module 1**: fixed conversion rate (1 GBP = 105.50 INR) per project
  baseline; median rating imputation and price-row dropping documented and
  justified by measured missing percentages.
- **Module 2**: leak-free `ColumnTransformer`/`Pipeline` architecture;
  Random Forest (tuned via `GridSearchCV`) selected as the deployed
  classifier based on highest F1/accuracy on held-out test data.
- **Module 3**: fully offline, deterministic `MOCK_LLM` baseline using
  ChromaDB + `all-MiniLM-L6-v2` for retrieval; optional real-LLM path
  implemented but not required for grading.

## Git Workflow

A feature branch was created, committed to multiple times, and merged back
into `main` for each module (`feature/data-pipeline`, `feature/analytics`,
`feature/support-assistant`), satisfying the repository-wide branch/merge
requirement.