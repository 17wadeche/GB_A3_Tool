from __future__ import annotations
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
from a3_autopilot.dmaic import orchestrate_dmaic
from a3_autopilot.ingestion import load_dataset
from a3_autopilot.models import DefineInput, GoalMetric, MeasureInput, TeamMember
from a3_autopilot.slide_builder import render_single_slide
def main() -> None:
    example_path = Path("examples/example_input.csv")
    output_path = Path("examples/sample_a3_single_slide.pptx")
    dataset, mapping = load_dataset(example_path)
    define = DefineInput(
        problem_statement="Late shipment defects exceed customer commitment threshold",
        business_impact="Expedite cost and customer complaints increased",
        scope_in="Order pick-pack-ship workflow",
        scope_out="Supplier lead-time changes",
        goal_metric=GoalMetric(
            metric_name="Late shipment defects",
            baseline=float(pd.to_numeric(dataset[mapping["impact"]], errors="coerce").mean()),
            target=15,
            due_date=date.today() + timedelta(days=90),
        ),
        team=[
            TeamMember(name="Alex", role="Champion"),
            TeamMember(name="Priya", role="Process Owner"),
            TeamMember(name="Sam", role="Analyst"),
        ],
    )
    pkg = orchestrate_dmaic(
        define_input=define,
        measure_input=MeasureInput(dataset_present=True, field_mapping=mapping),
        dataset=dataset,
        output_dir="examples",
    )
    render_single_slide(pkg, output_path)
    print(f"Generated: {output_path}")
if __name__ == "__main__":
    main()
