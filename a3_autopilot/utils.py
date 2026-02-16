from __future__ import annotations

from datetime import date

import pandas as pd


def normalize_column(col: str) -> str:
    return "_".join(col.strip().lower().split())


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    copy_df = df.copy()
    copy_df.columns = [normalize_column(str(c)) for c in copy_df.columns]
    return copy_df


def to_date_or_default(value: str | None, default: date) -> date:
    if not value:
        return default
    return pd.to_datetime(value).date()
