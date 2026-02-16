from datetime import date

from pptx import Presentation

from a3_autopilot.dmaic import orchestrate_dmaic
from a3_autopilot.models import DefineInput, GoalMetric, MeasureInput, TeamMember
from a3_autopilot.slide_builder import render_single_slide


def test_single_slide_export(tmp_path):
    define = DefineInput(
        problem_statement="Lead time variation",
        business_impact="Margin erosion",
        scope_in="Order processing",
        scope_out="Market demand",
        goal_metric=GoalMetric(metric_name="Lead time", baseline=15, target=10, due_date=date.today()),
        team=[TeamMember(name="Alex", role="Champion")],
    )
    pkg = orchestrate_dmaic(define, MeasureInput(dataset_present=False), dataset=None, output_dir=tmp_path)
    output = tmp_path / "out.pptx"
    render_single_slide(pkg, output)

    prs = Presentation(str(output))
    assert len(prs.slides) == 1
