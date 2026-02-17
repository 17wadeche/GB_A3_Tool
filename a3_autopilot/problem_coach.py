from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List


@dataclass
class ProblemStatementFeedback:
    score: int
    strengths: List[str]
    missing_components: List[str]
    suggested_rewrite: str


@dataclass
class DefineDraft:
    project_y: str
    goal_statement: str
    do_not_harm: str
    business_impact: str
    scope_in: str
    scope_out: str
    goal_metric: str
    baseline: float
    target: float
    due_date: date


EXAMPLE_PROBLEM_STATEMENT = (
    "Between January and March 2026, the Medtronic Cardiac Rhythm Management complaint intake "
    "process at the Mounds View site logged 148 complaint records with 34% missing mandatory "
    "fields at first pass, causing an average 2.1-day delay in regulatory triage and increasing "
    "risk of late MDR submission."
)


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(k in text for k in keywords)


def _extract_percent(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if match:
        return float(match.group(1))
    return None


def _extract_days(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*day", text)
    if match:
        return float(match.group(1))
    return None


def build_define_draft(statement: str) -> DefineDraft:
    text = (statement or "").strip()
    lowered = text.lower()

    percent = _extract_percent(text)
    days = _extract_days(text)

    project_y = "Complaint Handling Cycle Time and First-Pass Completeness"
    goal_metric = "First-pass complete complaint records (%)"
    baseline = 100.0 - percent if percent is not None else 70.0
    target = min(99.0, baseline + 15.0)

    if "delay" in lowered and days is not None:
        project_y = "Complaint Intake to Regulatory Triage Lead Time"
        goal_metric = "Average complaint triage lead time (days)"
        baseline = days
        target = max(0.5, round(days * 0.5, 2))

    business_impact = (
        "Current complaint handling performance increases compliance risk, slows response time, and may "
        "impact patient safety and audit readiness."
    )
    if "mdr" in lowered or "regulatory" in lowered:
        business_impact = (
            "Delayed or incomplete complaint handling creates risk of late regulatory reporting and "
            "inspection findings."
        )

    scope_in = "Complaint intake, data entry, and quality review"
    scope_out = "CAPA implementation and post-market trend governance"

    return DefineDraft(
        project_y=project_y,
        goal_statement=(
            f"Improve {goal_metric} from {baseline:.1f} to {target:.1f} by {date.today() + timedelta(days=90)}."
        ),
        do_not_harm=(
            "Do not reduce complaint quality, regulatory compliance, or patient safety while improving speed."
        ),
        business_impact=business_impact,
        scope_in=scope_in,
        scope_out=scope_out,
        goal_metric=goal_metric,
        baseline=baseline,
        target=target,
        due_date=date.today() + timedelta(days=90),
    )


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
