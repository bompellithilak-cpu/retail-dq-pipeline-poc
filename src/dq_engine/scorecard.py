"""
Turns per-row rule results into a DQ scorecard: pass rate per rule,
pass rate per dimension, an overall score, and the list of failing rows
per rule (for triage).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from src.dq_engine.rules import RULE_CATALOG


@dataclass
class RuleResult:
    rule_name: str
    dimension: str
    total_rows: int
    passed_rows: int
    pass_rate: float
    failing_row_ids: list = field(default_factory=list)


@dataclass
class DQScorecard:
    generated_at: str
    total_rows: int
    overall_score: float
    dimension_scores: dict
    rule_results: list

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "total_rows": self.total_rows,
            "overall_score": round(self.overall_score, 4),
            "dimension_scores": {k: round(v, 4) for k, v in self.dimension_scores.items()},
            "rule_results": [
                {
                    "rule_name": r.rule_name,
                    "dimension": r.dimension,
                    "total_rows": r.total_rows,
                    "passed_rows": r.passed_rows,
                    "pass_rate": round(r.pass_rate, 4),
                    "failing_row_ids": r.failing_row_ids,
                }
                for r in self.rule_results
            ],
        }


def run_rules(
    df: pd.DataFrame,
    stores_ref: pd.DataFrame,
    customers_ref: pd.DataFrame,
    id_column: str = "order_id",
) -> list[RuleResult]:
    """Execute every rule in RULE_CATALOG against df, return one RuleResult each."""
    results: list[RuleResult] = []
    total = len(df)

    for rule_name, (dimension, rule_fn) in RULE_CATALOG.items():
        outcome = rule_fn(df, stores_ref=stores_ref, customers_ref=customers_ref)
        passed = int(outcome.sum())
        failing_ids = df.loc[~outcome, id_column].astype(str).tolist()
        results.append(
            RuleResult(
                rule_name=rule_name,
                dimension=dimension,
                total_rows=total,
                passed_rows=passed,
                pass_rate=(passed / total) if total else 1.0,
                failing_row_ids=failing_ids,
            )
        )
    return results


def build_scorecard(
    rule_results: list[RuleResult], total_rows: int, generated_at: str
) -> DQScorecard:
    """Roll rule-level results up into dimension scores and an overall score."""
    by_dimension: dict[str, list[RuleResult]] = {}
    for r in rule_results:
        by_dimension.setdefault(r.dimension, []).append(r)

    dimension_scores = {
        dim: sum(r.pass_rate for r in rules) / len(rules) for dim, rules in by_dimension.items()
    }
    overall_score = (
        sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 1.0
    )

    return DQScorecard(
        generated_at=generated_at,
        total_rows=total_rows,
        overall_score=overall_score,
        dimension_scores=dimension_scores,
        rule_results=rule_results,
    )
