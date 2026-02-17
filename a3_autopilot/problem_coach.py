from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Literal

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


@dataclass
class LeanToolGuidance:
    tool_name: str
    when_to_use: str
    output_expected: str
    starter_prompt: str


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
    else:
        project_y = "Process Effectiveness and On-Time Execution"
        goal_metric = "On-time completion rate (%)"
        baseline = percent if percent is not None else 65.0
        target = min(98.0, baseline + 20.0)
        business_impact = "Execution friction drives delays, rework, missed commitments, and reduced team productivity."
        scope_in = "Process intake, handoffs, and execution"
        scope_out = "Out-of-scope upstream/downstream systems not controlled by this team"
        do_not_harm = "Do not increase burnout, defect rates, customer impact, or compliance risk while improving speed."

        if "a3" in lowered:
            project_y = "A3 Process Effectiveness"
            goal_metric = "A3 completion rate (%)"
            baseline = percent if percent is not None else 60.0
            target = min(95.0, baseline + 20.0)
            business_impact = "A complex A3 process lowers adoption, completion, and quality of problem-solving outcomes."
            scope_in = "A3 workflow from kickoff through approval"
            scope_out = "Non-A3 methods and unrelated training programs"
            do_not_harm = "Do not reduce rigor, coaching quality, or learning depth while simplifying the process."

        if days is not None and "delay" in lowered:
            goal_metric = "Average cycle time (days)"
            baseline = days
            target = max(0.5, round(days * 0.6, 2))

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
        strengths.append("Project Y is defined.")
    else:
        improvements.append("Add Project Y (primary output variable being improved).")

    if goal_statement.strip():
        strengths.append("Goal statement is present.")
    else:
        improvements.append("Add a SMART goal statement with baseline, target, and due date.")

    if do_not_harm.strip():
        strengths.append("Do-not-harm guardrails are defined.")
    else:
        improvements.append("Add do-not-harm constraints to protect quality, safety, and customer impact.")

    if business_impact.strip():
        strengths.append("Business impact is described.")
    else:
        improvements.append("Describe business impact (delivery, quality, cost, safety, compliance, productivity).")

    if scope_in.strip() and scope_out.strip():
        strengths.append("Scope in and scope out are both defined.")
    else:
        improvements.append("Define both scope in and scope out boundaries.")

    if goal_metric.strip():
        strengths.append("Goal metric is specified.")
    else:
        improvements.append("Define a measurable goal metric.")

    if baseline > 0 and target > 0:
        strengths.append("Baseline and target values are numeric and non-zero.")
        if baseline != target:
            strengths.append("Baseline and target indicate a measurable gap.")
        else:
            improvements.append("Set target different from baseline to reflect improvement.")
    else:
        improvements.append("Provide non-zero baseline and target values.")

    score = max(0, min(100, int((len(strengths) / 8) * 100)))
    return DefineSectionFeedback(strengths=strengths, improvements=improvements, score=score)


def rewrite_problem_statement(statement: str) -> str:
    text = (statement or "").strip()
    if not text:
        return "From [time period], in [process], [issue] occurs at [measured magnitude], resulting in [impact]."

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
    evidence = "frequent variation and delays"
    if percent is not None:
        evidence = f"a measurable gap of {percent:.1f}%"
    elif days is not None:
        evidence = f"an average delay of {days:.1f} days"

    if context == "complaint_handling":
        location = "in the complaint handling workflow"
        default_impact = "increased compliance risk, slower triage, and potential patient impact"
    else:
        location = "in the current process"
        default_impact = "missed commitments, rework, and reduced performance"

    impact = impact_sentence if impact_sentence else default_impact
    return f"{timeframe}, {location}, {issue_sentence}. Evidence includes {evidence}. This results in {impact}."


def rewrite_define_fields(fields: Dict[str, str]) -> Dict[str, str]:
    rewrites: Dict[str, str] = {}
    problem = fields.get("problem_statement", "")
    if problem.strip():
        rewrites["problem_statement"] = rewrite_problem_statement(problem)

    if fields.get("project_y", "").strip():
        rewrites["project_y"] = f"Primary output (Y): {fields['project_y'].strip()}"

    if fields.get("goal_statement", "").strip():
        gs = fields["goal_statement"].strip().rstrip(".")
        rewrites["goal_statement"] = f"SMART Goal: {gs}."

    if fields.get("do_not_harm", "").strip():
        rewrites["do_not_harm"] = f"Constraint: {fields['do_not_harm'].strip().rstrip('.')}"

    if fields.get("business_impact", "").strip():
        rewrites["business_impact"] = f"Business impact: {fields['business_impact'].strip().rstrip('.')}"

    if fields.get("scope_in", "").strip():
        rewrites["scope_in"] = f"In scope: {fields['scope_in'].strip()}"
    if fields.get("scope_out", "").strip():
        rewrites["scope_out"] = f"Out of scope: {fields['scope_out'].strip()}"
    if fields.get("goal_metric", "").strip():
        rewrites["goal_metric"] = f"Primary metric: {fields['goal_metric'].strip()}"

    return rewrites


def evaluate_problem_statement(statement: str) -> ProblemStatementFeedback:
    text = (statement or "").strip()
    lowered = text.lower()
    context = detect_context(text)

    strengths: List[str] = []
    missing: List[str] = []

    has_where = _contains_any(lowered, ["site", "department", "process", "team", "workflow", "line", "function"])
    has_when = _contains_any(
        lowered,
        ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "week", "month", "quarter", "q1", "q2", "q3", "q4", "202"],
    )
    has_what = _contains_any(lowered, ["complaint", "defect", "error", "delay", "difficult", "slow", "complex", "burdensome", "variation", "waste"])
    has_magnitude = _contains_any(lowered, ["%", "percent", "days", "hours", "records", "count", "rate", "number"])
    has_impact = _contains_any(lowered, ["risk", "impact", "cost", "delay", "rework", "productivity", "missed", "quality", "safety", "compliance"])

    if len(text.split()) >= 20:
        strengths.append("Statement is detailed enough to understand context.")
    else:
        missing.append("Add more detail (aim for at least 20 words).")

    if has_where:
        strengths.append("Includes process/organization context.")
    else:
        missing.append("Specify where the problem occurs (process/team/function).")

    if has_when:
        strengths.append("Includes a time window or period.")
    else:
        missing.append("Add a clear time frame (month/quarter/date range).")

    if has_what:
        strengths.append("Clearly names the core issue.")
    else:
        missing.append("Name the core issue explicitly.")

    if has_magnitude:
        strengths.append("Contains measurable magnitude.")
    else:
        missing.append("Add measurable data such as %, count, rate, or cycle time.")

    if has_impact:
        strengths.append("States why the issue matters.")
    else:
        missing.append("Explain impact (delivery, quality, cost, safety, compliance, productivity).")

    score = max(0, min(100, int((len(strengths) / 6) * 100)))
    rewrite_template = (
        "From [time period], in [team/process], [issue] occurs at [measured magnitude], "
        "resulting in [delivery/quality/cost/safety/compliance impact]."
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
        suggested_rewrite=rewrite_template,
        detected_context=context,
    )


def generate_lean_tool_guidance(problem_statement: str) -> List[LeanToolGuidance]:
    context = detect_context(problem_statement)
    focus = "complaint handling flow" if context == "complaint_handling" else "end-to-end process flow"

    return [
        LeanToolGuidance(
            tool_name="VOC + CTQ Tree",
            when_to_use="Define phase to translate stakeholder/customer needs into measurable CTQs.",
            output_expected="Prioritized VOC themes, CTQ requirements, and measurable specs.",
            starter_prompt=f"Build a VOC-to-CTQ tree for the {focus}. Include top 5 needs and CTQ metrics.",
        ),
        LeanToolGuidance(
            tool_name="SIPOC + High-Level Process Map",
            when_to_use="Early Define/Measure to align scope, suppliers, inputs, process, outputs, customers.",
            output_expected="One-page SIPOC and 6-10 step process map with handoffs.",
            starter_prompt=f"Create a SIPOC and high-level process map for the {focus}.",
        ),
        LeanToolGuidance(
            tool_name="Value Stream Mapping (Current/Future State)",
            when_to_use="Measure/Analyze to identify wait time, rework loops, bottlenecks, and flow losses.",
            output_expected="Current-state VSM with cycle/lead times and a future-state VSM with kaizen bursts.",
            starter_prompt="Draft current and future-state VSM including takt time, cycle time, queue time, and bottlenecks.",
        ),
        LeanToolGuidance(
            tool_name="Process Mapping (Swimlane)",
            when_to_use="Analyze to identify role-based handoff failures and unclear ownership.",
            output_expected="Swimlane map with decision points, rework loops, and ownership clarity.",
            starter_prompt="Create a swimlane process map and highlight non-value-added steps and rework loops.",
        ),
        LeanToolGuidance(
            tool_name="MSA + Capability + Control Plan",
            when_to_use="Measure/Control for metric reliability and sustainment of gains.",
            output_expected="MSA summary, capability view (Cp/Cpk/Ppk where relevant), and control response plan.",
            starter_prompt="Generate an MSA checklist, capability analysis plan, and control plan for key CTQ metrics.",
        ),
    ]


def answer_coaching_question(question: str, define_snapshot: Dict[str, str]) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "Ask a specific Lean Six Sigma/DMAIC question and I will coach you with actionable steps."

    if "voc" in q:
        return "VOC captures stakeholder voice (pain points, needs, expectations). Convert VOC to CTQs by making each need measurable (metric + spec + owner + review cadence)."
    if "value stream" in q or "vsm" in q:
        return "Start with a current-state VSM: process steps, cycle time, wait time, queue, rework. Then build future-state VSM by removing bottlenecks and adding pull/flow controls."
    if "process map" in q or "swimlane" in q:
        return "Use a swimlane map with roles, handoffs, and decisions. Mark rework loops, delays, and unclear ownership. Those become root-cause candidates."
    if "goal" in q:
        current_goal = define_snapshot.get("goal_statement", "").strip()
        return f"A Black Belt-level goal should be SMART and CTQ-linked. Current goal: '{current_goal or 'Not provided'}'. Ensure baseline, target, due date, and business impact are explicit."

    return "Use Define→Measure→Analyze→Improve→Control discipline: clarify CTQs, baseline capability, validate root causes, test countermeasures, then lock in controls with owner/cadence/response plan."
