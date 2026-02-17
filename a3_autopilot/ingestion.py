from __future__ import annotations
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
import pandas as pd
from a3_autopilot.utils import normalize_dataframe_columns
CANONICAL_FIELDS = {
    "category": ["category", "defect_type", "issue", "reason", "problem", "type"],
    "impact": ["count", "defect_count", "cost", "impact", "qty", "quantity", "volume", "amount"],
    "date": ["date", "created_date", "timestamp", "event_date"],
    "process_step": ["process_step", "step", "stage", "operation", "workcenter"],
    "owner": ["owner", "assignee", "team_member", "operator", "lead"],
}
def _detect_columns(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for canonical, aliases in CANONICAL_FIELDS.items():
        for col in columns:
            if col in aliases or any(alias in col for alias in aliases):
                mapping[canonical] = col
                break
    if "impact" not in mapping:
        numeric_candidates = [c for c in columns if any(k in c for k in ["count", "qty", "cost", "impact", "amount"])]
        if numeric_candidates:
            mapping["impact"] = numeric_candidates[0]
    if "category" not in mapping:
        category_candidates = [c for c in columns if any(k in c for k in ["category", "reason", "issue", "type"])]
        if category_candidates:
            mapping["category"] = category_candidates[0]
    return mapping
def load_dataset(uploaded_file: BinaryIO | BytesIO | str | Path) -> tuple[pd.DataFrame, dict[str, str]]:
    if isinstance(uploaded_file, (str, Path)):
        path = Path(uploaded_file)
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
    else:
        filename = getattr(uploaded_file, "name", "uploaded.csv")
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    df = normalize_dataframe_columns(df)
    df = df.dropna(how="all")
    mapping = _detect_columns(df.columns.tolist())
    if "impact" in mapping:
        df[mapping["impact"]] = pd.to_numeric(df[mapping["impact"]], errors="coerce").fillna(0)
    if "category" in mapping:
        df[mapping["category"]] = df[mapping["category"]].fillna("Unknown")
    return df, mapping
