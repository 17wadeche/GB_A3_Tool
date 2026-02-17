from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ProblemStatementFeedback:
    score: int
    strengths: List[str]
    missing_components: List[str]
    suggested_rewrite: str


EXAMPLE_PROBLEM_STATEMENT = (
    "Between January and March 2026, the Medtronic Cardiac Rhythm Management complaint intake "
    "process at the Mounds View site logged 148 complaint records with 34% missing mandatory "
    "fields at first pass, causing an average 2.1-day delay in regulatory triage and increasing "
    "risk of late MDR submission."
)


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(k in text for k in keywords)


def evaluate_problem_statement(statement: str) -> ProblemStatementFeedback:
    text = (statement or "").strip()
    lowered = text.lower()

    strengths: List[str] = []
    missing: List[str] = []

    has_where = _contains_any(lowered, ["medtronic", "site", "plant", "department", "process"])
    has_when = _contains_any(
        lowered,
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
            "week",
            "month",
            "quarter",
            "q1",
            "q2",
            "q3",
            "q4",
            "202",
        ],
    )
    has_what = _contains_any(lowered, ["complaint", "nonconformance", "defect", "error", "delay"])
    has_magnitude = _contains_any(lowered, ["%", "percent", "days", "hours", "records", "cases", "incidents"])
    has_impact = _contains_any(lowered, ["risk", "impact", "cost", "delay", "regulatory", "patient", "mdr", "compliance"])

    if len(text.split()) >= 20:
        strengths.append("Statement is detailed enough to understand context.")
    else:
        missing.append("Add more detail (aim for at least 20 words).")

    if has_where:
        strengths.append("Includes process/organization context (where the issue happens).")
    else:
        missing.append("Specify where the problem occurs (team, process, product line, or site).")

    if has_when:
        strengths.append("Includes a time window or period.")
    else:
        missing.append("Add a clear time frame (for example, Jan-Mar 2026 or Q1 2026).")

    if has_what:
        strengths.append("Clearly names the performance issue.")
    else:
        missing.append("Name the core issue explicitly (for example, complaint intake delays or missing fields).")

    if has_magnitude:
        strengths.append("Contains measurable magnitude (count, rate, or time).")
    else:
        missing.append("Add measurable data such as %, count, rate, or delay duration.")

    if has_impact:
        strengths.append("States why the issue matters (business/patient/regulatory impact).")
    else:
        missing.append("Explain impact (compliance risk, patient risk, cost, or lead-time impact).")

    score = max(0, min(100, int((len(strengths) / 6) * 100)))

    if not text:
        rewrite = EXAMPLE_PROBLEM_STATEMENT
    else:
        rewrite = (
            "From [time period], in the Medtronic [site/team/process], [problem] occurs at "
            "[measured magnitude], resulting in [business/regulatory/patient impact]."
        )

    return ProblemStatementFeedback(
        score=score,
        strengths=strengths,
        missing_components=missing,
        suggested_rewrite=rewrite,
    )
