from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from a3_autopilot.assumptions import add_assumption
from a3_autopilot.charter import generate_project_charter
from a3_autopilot.fishbone import build_fishbone
from a3_autopilot.five_whys import derive_root_causes, generate_five_whys
from a3_autopilot.models import (
    ActionItem,
    Assumption,
    ControlPlan,
    Countermeasure,
    DefineInput,
    DmaicPackage,
    MeasureInput,
)
from a3_autopilot.pareto import build_pareto, save_pareto_chart
from a3_autopilot.scoring import confidence_notes_from_data


def orchestrate_dmaic(
    define_input: DefineInput,
    measure_input: MeasureInput,
    dataset: pd.DataFrame | None,
    output_dir: str | Path = "examples",
) -> DmaicPackage:
    assumptions: list[Assumption] = []
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    measure_summary: dict[str, float | str] = {}

    category_col = measure_input.field_mapping.get("category", "category")
    impact_col = measure_input.field_mapping.get("impact", "impact")

    if dataset is None or dataset.empty or category_col not in dataset.columns or impact_col not in dataset.columns:
        add_assumption(
            assumptions,
            "No validated dataset supplied; baseline distribution synthesized from guided input.",
            "Missing upload or missing mapped columns",
        )
        dataset = pd.DataFrame(
            {
                "category": ["Delay", "Rework", "Defect", "Handoff", "Wait"],
                "impact": [25, 18, 14, 10, 7],
                "process_step": ["Fulfillment", "QA", "Assembly", "Handoff", "Review"],
            }
        )
        category_col, impact_col = "category", "impact"

    pareto_df = build_pareto(dataset, category_col, impact_col)
    chart_path = save_pareto_chart(pareto_df, category_col, impact_col, output_dir / "pareto.png")

    baseline_value = float(dataset[impact_col].mean()) if impact_col in dataset.columns else None
    measure_summary["baseline_mean_impact"] = round(baseline_value, 2) if baseline_value is not None else "N/A"
    measure_summary["records"] = int(len(dataset))
    measure_summary["project_charter"] = generate_project_charter(define_input)["goal"]

    top_signals = pareto_df.head(5)[category_col].astype(str).tolist()
    whys = generate_five_whys(define_input.problem_statement, top_signals)
    root_causes = derive_root_causes(whys, pareto_df)

    fishbone = build_fishbone(define_input.problem_statement, root_causes)

    countermeasures = []
    for i, rc in enumerate(root_causes):
        countermeasures.append(
            Countermeasure(
                id=f"CM-{i+1}",
                description=f"Standardize control for: {rc.statement[:60]}",
                linked_root_cause_ids=[rc.id],
                impact=max(1, 9 - i),
                effort=min(10, 3 + i),
                risk=min(10, 2 + i),
            )
        )

    team_names = [m.name for m in define_input.team] or ["Process Owner", "Analyst"]
    accountable = team_names[0]

    actions = []
    for idx, cm in enumerate(countermeasures[:3]):
        actions.append(
            ActionItem(
                action=cm.description,
                owner=team_names[idx % len(team_names)],
                due_date=date.today() + timedelta(days=14 * (idx + 1)),
                kpi=define_input.goal_metric.metric_name,
                control_method="Weekly control chart review + escalation rule",
                responsible=[team_names[idx % len(team_names)]],
                accountable=accountable,
                consulted=team_names[1:2],
                informed=team_names[2:3],
            )
        )

    control_plan = ControlPlan(
        cadence="Weekly KPI review",
        response_plan="If KPI misses threshold 2 periods, trigger root cause check and leader review",
        standard_work_update="Update SOP and checklist with new controls",
        audit_frequency="Monthly layered process audit",
    )

    score, notes = confidence_notes_from_data(measure_input.dataset_present, len(root_causes))

    return DmaicPackage(
        define=define_input,
        measure_summary=measure_summary,
        pareto_rows=pareto_df.to_dict(orient="records"),
        pareto_chart_path=chart_path,
        fishbone=fishbone,
        five_whys=whys,
        root_causes=root_causes,
        countermeasures=countermeasures,
        actions=actions,
        control_plan=control_plan,
        assumptions=assumptions,
        confidence_score=score,
        confidence_notes=notes,
    )
