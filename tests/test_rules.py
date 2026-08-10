"""Unit tests for individual DQ rules in src/dq_engine/rules.py."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.dq_engine import rules


def test_not_null_flags_missing_values():
    df = pd.DataFrame({"order_id": ["O1", None, "O3", "  "]})
    result = rules.not_null(df, "order_id")
    assert result.tolist() == [True, False, True, False]


def test_unique_order_id_flags_duplicates():
    df = pd.DataFrame({"order_id": ["O1", "O2", "O1", "O3"]})
    result = rules.unique_order_id(df)
    assert result.tolist() == [False, True, False, True]


def test_valid_email_accepts_good_and_rejects_bad():
    df = pd.DataFrame({"email": ["a@b.com", "not-an-email", "x.y@z.co"]})
    result = rules.valid_email(df)
    assert result.tolist() == [True, False, True]


def test_positive_quantity_rejects_zero_and_negative():
    df = pd.DataFrame({"quantity": [1, 0, -3, 5]})
    result = rules.positive_quantity(df)
    assert result.tolist() == [True, False, False, True]


def test_non_negative_price_allows_zero_rejects_negative():
    df = pd.DataFrame({"unit_price": [0, 10.5, -1]})
    result = rules.non_negative_price(df)
    assert result.tolist() == [True, True, False]


def test_order_date_not_future():
    df = pd.DataFrame({"order_date": ["2020-01-01", "2999-01-01"]})
    as_of = datetime(2026, 8, 10)
    result = rules.order_date_not_future(df, as_of=as_of)
    assert result.tolist() == [True, False]


def test_known_store_id():
    df = pd.DataFrame({"store_id": ["S001", "S999"]})
    stores_ref = pd.DataFrame({"store_id": ["S001", "S002"]})
    result = rules.known_store_id(df, stores_ref)
    assert result.tolist() == [True, False]


def test_known_customer_id():
    df = pd.DataFrame({"customer_id": ["C001", "C999"]})
    customers_ref = pd.DataFrame({"customer_id": ["C001", "C002"]})
    result = rules.known_customer_id(df, customers_ref)
    assert result.tolist() == [True, False]
