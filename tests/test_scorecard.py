"""Unit tests for scorecard aggregation and the end-to-end pipeline."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.dq_engine.pipeline import run_pipeline
from src.dq_engine.scorecard import build_scorecard, run_rules


def test_run_rules_returns_one_result_per_catalog_entry():
    orders = pd.DataFrame(
        {
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C2"],
            "order_date": ["2026-08-01", "2026-08-02"],
            "product_sku": ["SKU-1", "SKU-2"],
            "quantity": [1, 2],
            "unit_price": [10.0, 20.0],
            "store_id": ["S1", "S1"],
            "email": ["a@b.com", "c@d.com"],
        }
    )
    stores_ref = pd.DataFrame({"store_id": ["S1"]})
    customers_ref = pd.DataFrame({"customer_id": ["C1", "C2"]})

    results = run_rules(orders, stores_ref, customers_ref)
    assert len(results) == 11  # matches RULE_CATALOG size
    assert all(r.pass_rate == 1.0 for r in results)


def test_build_scorecard_overall_score_is_average_of_dimensions():
    orders = pd.DataFrame(
        {
            "order_id": ["O1", "O1"],  # duplicate -> fails uniqueness
            "customer_id": ["C1", "C2"],
            "order_date": ["2026-08-01", "2026-08-02"],
            "product_sku": ["SKU-1", "SKU-2"],
            "quantity": [1, 2],
            "unit_price": [10.0, 20.0],
            "store_id": ["S1", "S1"],
            "email": ["a@b.com", "c@d.com"],
        }
    )
    stores_ref = pd.DataFrame({"store_id": ["S1"]})
    customers_ref = pd.DataFrame({"customer_id": ["C1", "C2"]})

    results = run_rules(orders, stores_ref, customers_ref)
    scorecard = build_scorecard(
        results, total_rows=len(orders), generated_at="2026-08-10T00:00:00Z"
    )

    assert scorecard.dimension_scores["uniqueness"] == 0.0
    assert 0.0 < scorecard.overall_score < 1.0


def test_run_pipeline_end_to_end_flags_seeded_bad_rows(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "dq_scorecard.json"

    result = run_pipeline(data_dir=repo_root / "data", output_path=output_path)

    assert output_path.exists()
    assert result["total_rows"] == 15
    # The seeded dataset has known violations in every dimension, so no
    # dimension should score a perfect 1.0.
    for dimension_score in result["dimension_scores"].values():
        assert dimension_score < 1.0
    # unique_order_id must catch the seeded duplicate "O003" rows.
    unique_rule = next(r for r in result["rule_results"] if r["rule_name"] == "unique_order_id")
    assert "O003" in unique_rule["failing_row_ids"]
