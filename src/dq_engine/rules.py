"""
Rule catalog for the retail orders DQ pipeline.

Each rule function takes the orders DataFrame (+ reference tables where
needed) and returns a Series of booleans, one per row: True = row passes.

Dimensions covered:
    completeness  -> not_null_*
    validity      -> valid_email, positive_quantity, non_negative_price,
                      order_date_not_future
    uniqueness    -> unique_order_id
    integrity     -> known_store_id, known_customer_id
"""
from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def not_null(df: pd.DataFrame, column: str) -> pd.Series:
    """Completeness: column must not be null or an empty string."""
    return df[column].notna() & (df[column].astype(str).str.strip() != "")


def unique_order_id(df: pd.DataFrame) -> pd.Series:
    """Uniqueness: order_id must not repeat within the batch."""
    return ~df["order_id"].duplicated(keep=False)


def valid_email(df: pd.DataFrame) -> pd.Series:
    """Validity: email must match a basic RFC-5322-ish shape."""
    return df["email"].astype(str).str.match(EMAIL_RE)


def positive_quantity(df: pd.DataFrame) -> pd.Series:
    """Validity: quantity must be a positive integer."""
    qty = pd.to_numeric(df["quantity"], errors="coerce")
    return qty.notna() & (qty > 0)


def non_negative_price(df: pd.DataFrame) -> pd.Series:
    """Validity: unit_price must be zero or positive."""
    price = pd.to_numeric(df["unit_price"], errors="coerce")
    return price.notna() & (price >= 0)


def order_date_not_future(df: pd.DataFrame, as_of: datetime | None = None) -> pd.Series:
    """Validity: order_date cannot be in the future relative to as_of."""
    as_of = as_of or datetime.utcnow()
    dates = pd.to_datetime(df["order_date"], errors="coerce")
    return dates.notna() & (dates <= as_of)


def known_store_id(df: pd.DataFrame, stores_ref: pd.DataFrame) -> pd.Series:
    """Referential integrity: store_id must exist in the stores master table."""
    valid_ids = set(stores_ref["store_id"])
    return df["store_id"].isin(valid_ids)


def known_customer_id(df: pd.DataFrame, customers_ref: pd.DataFrame) -> pd.Series:
    """Referential integrity: customer_id must exist in the customers master table."""
    valid_ids = set(customers_ref["customer_id"])
    return df["customer_id"].isin(valid_ids)


RULE_CATALOG = {
    "not_null_order_id": ("completeness", lambda df, **_: not_null(df, "order_id")),
    "not_null_customer_id": ("completeness", lambda df, **_: not_null(df, "customer_id")),
    "not_null_order_date": ("completeness", lambda df, **_: not_null(df, "order_date")),
    "not_null_product_sku": ("completeness", lambda df, **_: not_null(df, "product_sku")),
    "unique_order_id": ("uniqueness", lambda df, **_: unique_order_id(df)),
    "valid_email": ("validity", lambda df, **_: valid_email(df)),
    "positive_quantity": ("validity", lambda df, **_: positive_quantity(df)),
    "non_negative_price": ("validity", lambda df, **_: non_negative_price(df)),
    "order_date_not_future": ("validity", lambda df, **_: order_date_not_future(df)),
    "known_store_id": (
        "integrity",
        lambda df, stores_ref=None, **_: known_store_id(df, stores_ref),
    ),
    "known_customer_id": (
        "integrity",
        lambda df, customers_ref=None, **_: known_customer_id(df, customers_ref),
    ),
}
