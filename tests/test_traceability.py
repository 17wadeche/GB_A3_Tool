from datetime import date

from a3_autopilot.dmaic import orchestrate_dmaic
from a3_autopilot.models import DefineInput, GoalMetric, MeasureInput, TeamMember
from a3_autopilot.scoring import quality_gate


def _define():
    return DefineInput(
        problem_statement="Escapes increased",
        business_impact="Customer credits rising",
        scope_in="Assembly",
        scope_out="Supplier",
        goal_metric=GoalMetric(metric_name="Escapes", baseline=12, target=5, due_date=date.today()),
        team=[TeamMember(name="Alex", role="Owner"), TeamMember(name="Priya", role="Analyst")],
    )


def test_countermeasures_link_to_root_causes_and_actions_complete(tmp_path):
    pkg = orchestrate_dmaic(_define(), MeasureInput(dataset_present=False), dataset=None, output_dir=tmp_path)
    root_ids = {rc.id for rc in pkg.root_causes}
    assert all(set(cm.linked_root_cause_ids).intersection(root_ids) for cm in pkg.countermeasures)
    assert all(a.owner and a.due_date and a.kpi and a.control_method for a in pkg.actions)
    assert any(cm.is_primary for cm in pkg.countermeasures)
    assert any(cm.is_backup for cm in pkg.countermeasures)
    assert pkg.traceability_graph["root_to_countermeasure"]
    passed, _ = quality_gate(pkg)
    assert passed
