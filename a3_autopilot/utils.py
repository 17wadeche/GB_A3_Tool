from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd


def normalize_column(col: str) -> str:
    return "_".join(col.strip().lower().replace("-", "_").split())


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    copy_df = df.copy()
    copy_df.columns = [normalize_column(str(c)) for c in copy_df.columns]
    return copy_df


def to_date_or_default(value: str | None, default: date) -> date:
    if not value:
        return default
    return pd.to_datetime(value).date()


def model_dump_compat(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()
