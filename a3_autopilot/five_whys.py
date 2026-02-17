from __future__ import annotations
from typing import Iterable
import pandas as pd
from a3_autopilot.models import FiveWhyNode, RootCause
def _confidence_from_support(support_count: int) -> float:
    return round(min(0.95, 0.35 + support_count * 0.1), 2)
def generate_five_whys(problem_statement: str, signals: Iterable[str]) -> list[FiveWhyNode]:
    signal_list = [s for s in signals if s]
    levels = min(5, max(3, len(signal_list)))
    whys: list[FiveWhyNode] = []
    current = problem_statement
    for i in range(levels):
        signal = signal_list[i] if i < len(signal_list) else "process variation"
        why_text = f"Because {signal.lower()} is not consistently controlled"
        evidence = f"Signal observed: {signal}"
        conf = _confidence_from_support(len(signal_list) - i)
        whys.append(FiveWhyNode(level=i + 1, why=why_text, evidence_note=evidence, confidence=conf))
        current = why_text
    return whys
def derive_root_causes(whys: list[FiveWhyNode], pareto_df: pd.DataFrame | None = None) -> list[RootCause]:
    roots: list[RootCause] = []
    categories = ["Method", "Man", "Measurement", "Machine", "Material", "Environment"]
    for idx, why in enumerate(whys[-3:]):
        evidence = why.evidence_note
        if pareto_df is not None and not pareto_df.empty:
            top = pareto_df.iloc[min(idx, len(pareto_df) - 1)]
            evidence = f"{why.evidence_note}; top contributor {top.iloc[0]}={top.iloc[1]}"
        roots.append(
            RootCause(
                id=f"RC-{idx+1}",
                category=categories[idx % len(categories)],
                statement=why.why,
                evidence_note=evidence,
                confidence=why.confidence,
            )
        )
    return roots
