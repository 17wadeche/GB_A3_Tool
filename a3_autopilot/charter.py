from __future__ import annotations
from a3_autopilot.models import DefineInput
def generate_project_charter(define: DefineInput) -> dict[str, str]:
    return {
        "problem": define.problem_statement,
        "project_y": define.project_y or "Not provided",
        "goal_statement": define.goal_statement or "Not provided",
        "do_not_harm": define.do_not_harm or "Not provided",
        "impact": define.business_impact or "Not provided",
        "scope_in": define.scope_in,
        "scope_out": define.scope_out,
        "goal": f"{define.goal_metric.metric_name} from {define.goal_metric.baseline if define.goal_metric.baseline is not None else 'current baseline'} to {define.goal_metric.target} by {define.goal_metric.due_date}",
        "team": ", ".join([f"{m.name} ({m.role})" for m in define.team]),
    }
