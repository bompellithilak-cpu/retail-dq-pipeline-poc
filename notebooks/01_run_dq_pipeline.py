# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # Retail Orders — Data Quality Pipeline
# MAGIC Runs the rule catalog in `src/dq_engine` against `data/orders_raw.csv`,
# MAGIC prints the DQ scorecard, and fails the job if the overall score drops
# MAGIC below the configured threshold.

# COMMAND ----------
dbutils.widgets.text("config_path", "configs/dev.yaml")
dbutils.widgets.text("run_env", "dev")

config_path = dbutils.widgets.get("config_path")
run_env = dbutils.widgets.get("run_env")
print(f"Running DQ pipeline | config_path={config_path} | run_env={run_env}")

# COMMAND ----------
from pathlib import Path

from src.dq_engine.pipeline import run_pipeline

# Databricks runs this notebook with cwd = the notebook's own folder
# (files/notebooks/), so the repo root is one level up from here.
repo_root = Path.cwd().parent
result = run_pipeline(
    data_dir=repo_root / "data",
    output_path=repo_root / "output" / "dq_scorecard.json",
)

# COMMAND ----------
print(f"Overall DQ score: {result['overall_score']:.2%}")
for dimension, score in result["dimension_scores"].items():
    print(f"  {dimension:>12}: {score:.2%}")

MIN_ACCEPTABLE_SCORE = 0.60
if result["overall_score"] < MIN_ACCEPTABLE_SCORE:
    raise ValueError(
        f"DQ score {result['overall_score']:.2%} is below the "
        f"{MIN_ACCEPTABLE_SCORE:.0%} threshold — failing the job so this "
        f"doesn't silently pass downstream."
    )
