from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Literal

ContextType = Literal["complaint_handling", "general"]


@dataclass
class ProblemStatementFeedback:
    score: int
    strengths: List[str]
    missing_components: List[str]
    suggested_rewrite: str
    detected_context: ContextType


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


@dataclass
class DefineSectionFeedback:
    strengths: List[str]
    improvements: List[str]
    score: int


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
    return float(match.group(1)) if match else None


def _extract_days(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*day", text.lower())
    return float(match.group(1)) if match else None


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def detect_context(statement: str) -> ContextType:
    lowered = (statement or "").lower()
    complaint_keywords = ["complaint", "mdr", "regulatory", "triage", "post-market", "vigilance", "adverse event"]
    return "complaint_handling" if _contains_any(lowered, complaint_keywords) else "general"


def build_define_draft(statement: str) -> DefineDraft:
    text = (statement or "").strip()
    lowered = text.lower()
    context = detect_context(text)
    percent = _extract_percent(text)
    days = _extract_days(text)
    due = date.today() + timedelta(days=90)

    if context == "complaint_handling":
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
            "Delayed or incomplete complaint handling increases compliance risk, slows response time, "
            "and can impact patient and audit outcomes."
        )
        scope_in = "Complaint intake, data entry, and quality review"
        scope_out = "CAPA implementation and post-market trend governance"
        do_not_harm = "Do not reduce complaint quality, regulatory compliance, or patient safety while improving speed."
    elif "a3" in lowered:
        project_y = "A3 Completion Rate and Process Simplicity"
        goal_metric = "A3 completion rate (%)"
        baseline = percent if percent is not None else 60.0
        target = min(95.0, baseline + 20.0)
        business_impact = (
            "An overly complex A3 process drives extra work and frustration, lowers completion rates, "
            "and reduces confidence in continuous-improvement execution."
        )
        scope_in = "A3 initiation, coaching touchpoints, and completion workflow"
        scope_out = "Non-A3 training programs and unrelated enterprise initiatives"
        do_not_harm = "Do not reduce coaching quality or problem-solving rigor while simplifying A3 execution."
    else:
        project_y = "Process Effectiveness and On-Time Execution"
        goal_metric = "On-time completion rate (%)"
        baseline = percent if percent is not None else 65.0
        target = min(98.0, baseline + 20.0)
        business_impact = "Execution friction drives delays, rework, missed commitments, and reduced team productivity."
        scope_in = "Work intake, prioritization, handoffs, and execution"
        scope_out = "Strategic planning and long-range portfolio decisions"
        do_not_harm = "Do not increase burnout, defect rates, or customer impact while improving speed."

    if days is not None and "delay" in lowered:
        goal_metric = "Average task completion lead time (days)" if context == "general" else goal_metric
        baseline = days
        target = max(0.5, round(days * 0.6, 2)) if context == "general" else target

    return DefineDraft(
        project_y=project_y,
        goal_statement=f"Improve {goal_metric} from {baseline:.1f} to {target:.1f} by {due}.",
        do_not_harm=do_not_harm,
        business_impact=business_impact,
        scope_in=scope_in,
        scope_out=scope_out,
        goal_metric=goal_metric,
        baseline=baseline,
        target=target,
        due_date=due,
    )


def assess_define_section(
    problem_statement: str,
    project_y: str,
    goal_statement: str,
    do_not_harm: str,
    business_impact: str,
    scope_in: str,
    scope_out: str,
    goal_metric: str,
    baseline: float,
    target: float,
) -> DefineSectionFeedback:
    strengths: List[str] = []
    improvements: List[str] = []

    if project_y.strip():
        strengths.append("Project Y is filled in.")
    else:
        improvements.append("Add Project Y (the primary output you are improving).")

    if goal_statement.strip():
        strengths.append("Goal statement is present.")
    else:
        improvements.append("Add a SMART goal statement with baseline, target, and due date.")

    if do_not_harm.strip():
        strengths.append("Do not harm guardrail is defined.")
    else:
        improvements.append("Add a 'Do not harm' guardrail to protect quality/safety/customer outcomes.")

    if business_impact.strip():
        strengths.append("Business impact is described.")
    else:
        improvements.append("Describe business impact (cost, delivery, quality, compliance, or productivity).")

    if scope_in.strip() and scope_out.strip():
        strengths.append("Scope boundaries are defined.")
    else:
        improvements.append("Fill both scope in and scope out to clarify boundaries.")

    if goal_metric.strip():
        strengths.append("Goal metric is provided.")
    else:
        improvements.append("Specify a goal metric (rate, time, defects, or completion).")

    if baseline > 0 and target > 0:
        strengths.append("Baseline and target are both numeric and non-zero.")
    else:
        improvements.append("Provide non-zero baseline and target values.")

    if baseline > 0 and target > 0 and baseline != target:
        strengths.append("Baseline and target show a clear improvement gap.")
    elif baseline > 0 and target > 0:
        improvements.append("Set target to be meaningfully different from baseline.")

    text = (problem_statement or "").lower()
    if goal_metric and not _contains_any(text, ["%", "rate", "day", "days", "time", "defect", "completion"]):
        improvements.append("Problem statement could include measurable language aligned to your goal metric.")

    total_checks = 8
    score = max(0, min(100, int((len(strengths) / total_checks) * 100)))
    return DefineSectionFeedback(strengths=strengths, improvements=improvements, score=score)


def rewrite_problem_statement(statement: str) -> str:
    text = (statement or "").strip()
    if not text:
        return EXAMPLE_PROBLEM_STATEMENT

    lowered = text.lower()
    context = detect_context(text)
    sentences = _split_sentences(text)

    issue_sentence = sentences[0].rstrip(".") if sentences else text.rstrip(".")
    impact_sentence = sentences[1].rstrip(".") if len(sentences) > 1 else ""
    impact_sentence = re.sub(r"^(this|it)\s+(leads to|results in|causes)\s+", "", impact_sentence, flags=re.IGNORECASE)

    has_time = _contains_any(
        lowered,
        ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "week", "month", "quarter", "q1", "q2", "q3", "q4", "202"],
    )
    timeframe = "Over the last quarter" if not has_time else "During the stated period"

    percent = _extract_percent(text)
    days = _extract_days(text)
    evidence = "frequent delays and extra work"
    if percent is not None:
        evidence = f"a measurable gap of {percent:.1f}%"
    elif days is not None:
        evidence = f"an average delay of {days:.1f} days"

    if context == "complaint_handling":
        location = "in the complaint handling workflow"
        default_impact = "higher compliance risk, slower triage, and potential patient impact"
    elif "a3" in lowered:
        location = "in the current A3 workflow"
        default_impact = "lower A3 completion rates and reduced value from the A3 method"
    else:
        location = "in the current team workflow"
        default_impact = "missed commitments, rework, and reduced productivity"

    impact = impact_sentence if impact_sentence else default_impact
    return f"{timeframe}, {location}, {issue_sentence}. Evidence includes {evidence}. This results in {impact}."


def evaluate_problem_statement(statement: str) -> ProblemStatementFeedback:
    text = (statement or "").strip()
    lowered = text.lower()
    context = detect_context(text)

    strengths: List[str] = []
    missing: List[str] = []

    has_where = _contains_any(lowered, ["site", "department", "process", "team", "workflow", "a3", "line"])
    has_when = _contains_any(
        lowered,
        ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "week", "month", "quarter", "q1", "q2", "q3", "q4", "202"],
    )
    has_what = _contains_any(lowered, ["complaint", "defect", "error", "delay", "difficult", "slow", "complex", "burdensome", "frustration"])
    has_magnitude = _contains_any(lowered, ["%", "percent", "days", "hours", "records", "count", "rate", "number"])
    has_impact = _contains_any(lowered, ["risk", "impact", "cost", "delay", "rework", "productivity", "missed", "frustration", "completion", "quality"])

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
        strengths.append("Clearly names the core issue.")
    else:
        missing.append("Name the core issue explicitly.")

    if has_magnitude:
        strengths.append("Contains measurable magnitude (count, rate, or time).")
    else:
        missing.append("Add measurable data such as %, count, rate, or delay duration.")

    if has_impact:
        strengths.append("States why the issue matters (impact).")
    else:
        missing.append("Explain the impact (compliance, cost, delay, quality, or productivity).")

    score = max(0, min(100, int((len(strengths) / 6) * 100)))

    rewrite_template = (
        "From [time period], in [team/process], [issue] occurs at [measured magnitude], "
        "resulting in [delivery/quality/cost/compliance/productivity impact]."
    )
    if context == "complaint_handling":
        rewrite_template = (
            "From [time period], in [complaint process/site], [complaint issue] occurs at [measured magnitude], "
            "resulting in [regulatory/patient/business impact]."
        )

    return ProblemStatementFeedback(
        score=score,
        strengths=strengths,
        missing_components=missing,
        suggested_rewrite=rewrite_template if text else EXAMPLE_PROBLEM_STATEMENT,
        detected_context=context,
    )
