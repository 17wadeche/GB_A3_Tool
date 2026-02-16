from __future__ import annotations

from a3_autopilot.models import DmaicPackage


def quality_gate(pkg: DmaicPackage) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if pkg.define.goal_metric.baseline is None and "baseline" not in str(pkg.measure_summary).lower():
        issues.append("baseline metric present")
    if not pkg.define.goal_metric.target or not pkg.define.goal_metric.due_date:
        issues.append("target metric + due date present")
    if not pkg.root_causes:
        issues.append("root cause linked to evidence")
    elif any(not rc.evidence_note for rc in pkg.root_causes):
        issues.append("root cause linked to evidence")

    root_ids = {rc.id for rc in pkg.root_causes}
    for cm in pkg.countermeasures:
        if not set(cm.linked_root_cause_ids).intersection(root_ids):
            issues.append("each countermeasure linked to root cause")
            break

    for action in pkg.actions:
        if not all([action.owner, action.due_date, action.kpi, action.control_method]):
            issues.append("each action has owner + due date + KPI + control step")
            break

    return len(issues) == 0, issues


def confidence_notes_from_data(has_dataset: bool, root_count: int) -> tuple[float, list[str]]:
    score = 0.55
    notes = []
    if has_dataset:
        score += 0.2
    else:
        notes.append("Upload defect/count/cost history to improve confidence.")
    if root_count >= 3:
        score += 0.15
    else:
        notes.append("More validated root-cause evidence would improve confidence.")
    score = round(min(score, 0.95), 2)
    return score, notes
