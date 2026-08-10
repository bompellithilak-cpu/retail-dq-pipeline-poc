# Retail DQ Pipeline POC

A rule-based Data Quality pipeline for retail order data, gated end-to-end
by CI/CD: lint -> unit tests -> SonarQube scan -> Quality Gate ->
Databricks Asset Bundle deploy -> DQ job run.

## What it checks

11 rules across 4 DQ dimensions, run against `data/orders_raw.csv`:

| Dimension    | Rules |
|---|---|
| Completeness | order_id, customer_id, order_date, product_sku not null |
| Uniqueness   | order_id has no duplicates |
| Validity     | email format, quantity > 0, unit_price >= 0, order_date not in the future |
| Integrity    | store_id exists in `stores_ref.csv`, customer_id exists in `customers_ref.csv` |

Output: `output/dq_scorecard.json` - per-rule pass rate, per-dimension
score, overall score, and the failing row IDs for triage.

## Run locally

```bash
pip install -r requirements-dev.txt
python -m src.dq_engine.pipeline
pytest --cov=src
```

## Pipeline

```
GitHub push -> lint (Ruff/Black/Flake8) -> pytest + coverage -> SonarQube scan
   -> Quality Gate check -> [passed] -> Databricks Asset Bundle deploy
   -> run dq_pipeline_job on Databricks
```

If the Quality Gate fails, deploy never runs (`needs: quality-gate` in the workflow).
