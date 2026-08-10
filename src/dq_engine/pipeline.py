"""
Entry point that ties the DQ engine together: load CSVs, run the rule
catalog, build a scorecard, write it out as JSON. Runs the same whether
invoked locally, in CI, or from the Databricks notebook wrapper.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pythonjsonlogger import jsonlogger

from src.dq_engine.scorecard import build_scorecard, run_rules

logger = logging.getLogger("dq_pipeline")


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(jsonlogger.JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def load_inputs(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    orders = pd.read_csv(data_dir / "orders_raw.csv")
    stores_ref = pd.read_csv(data_dir / "stores_ref.csv")
    customers_ref = pd.read_csv(data_dir / "customers_ref.csv")
    return orders, stores_ref, customers_ref


def run_pipeline(data_dir: Path, output_path: Path) -> dict:
    configure_logging()
    logger.info("dq_pipeline_started", extra={"data_dir": str(data_dir)})

    orders, stores_ref, customers_ref = load_inputs(data_dir)
    rule_results = run_rules(orders, stores_ref, customers_ref)
    generated_at = datetime.now(timezone.utc).isoformat()
    scorecard = build_scorecard(rule_results, total_rows=len(orders), generated_at=generated_at)

    result = scorecard.to_dict()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))

    logger.info(
        "dq_pipeline_completed",
        extra={"overall_score": result["overall_score"], "output_path": str(output_path)},
    )
    return result


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[2]
    scorecard_result = run_pipeline(
        data_dir=base / "data",
        output_path=base / "output" / "dq_scorecard.json",
    )
    print(json.dumps(scorecard_result, indent=2))
