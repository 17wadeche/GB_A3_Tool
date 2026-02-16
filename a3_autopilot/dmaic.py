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


def _select_countermeasure_priorities(countermeasures: list[Countermeasure]) -> list[Countermeasure]:
    for cm in countermeasures:
        cm.priority_score = round((cm.impact * 0.55) - (cm.effort * 0.25) - (cm.risk * 0.2), 2)
    ranked = sorted(countermeasures, key=lambda x: x.priority_score, reverse=True)
    if ranked:
        ranked[0].is_primary = True
    if len(ranked) > 1:
        ranked[1].is_backup = True
    return ranked


def _build_narrative(define_input: DefineInput, measure_summary: dict[str, float | str], root_count: int) -> dict[str, str]:
    return {
        "define": f"Problem: {define_input.problem_statement}. Scope in: {define_input.scope_in}; scope out: {define_input.scope_out}.",
        "measure": f"Baseline mean impact: {measure_summary.get('baseline_mean_impact', 'N/A')} from {measure_summary.get('records', 0)} records.",
        "analyze": f"Identified {root_count} validated root causes via Pareto, Fishbone, and 5 Whys.",
        "improve": "Primary and backup countermeasures selected using impact-effort-risk prioritization.",
        "control": "Control plan defines KPI cadence, audit frequency, response triggers, and standard work updates.",
    }


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
                "owner": ["Team", "Team", "Team", "Team", "Team"],
            }
        )
        category_col, impact_col = "category", "impact"

    pareto_df = build_pareto(dataset, category_col, impact_col)
    chart_path = save_pareto_chart(pareto_df, category_col, impact_col, output_dir / "pareto.png")

    baseline_value = float(dataset[impact_col].mean()) if impact_col in dataset.columns else None
    measure_summary["baseline_mean_impact"] = round(baseline_value, 2) if baseline_value is not None else "N/A"
    measure_summary["records"] = int(len(dataset))
    measure_summary["baseline_total_impact"] = round(float(dataset[impact_col].sum()), 2)
    measure_summary["vital_few_count"] = int(pareto_df["vital_few"].sum())
    measure_summary["project_charter"] = generate_project_charter(define_input)["goal"]

    top_signals = pareto_df.head(5)[category_col].astype(str).tolist()
    whys = generate_five_whys(define_input.problem_statement, top_signals)
    root_causes = derive_root_causes(whys, pareto_df)
    fishbone = build_fishbone(define_input.problem_statement, root_causes)

    countermeasures = [
        Countermeasure(
            id=f"CM-{i+1}",
            description=f"Deploy countermeasure for {rc.category.lower()}: {rc.statement[:64]}",
            linked_root_cause_ids=[rc.id],
            impact=max(1, 9 - i),
            effort=min(10, 3 + i),
            risk=min(10, 2 + i),
        )
        for i, rc in enumerate(root_causes)
    ]
    countermeasures = _select_countermeasure_priorities(countermeasures)

    team_names = [m.name for m in define_input.team] or ["Process Owner", "Analyst"]
    accountable = team_names[0]

    actions: list[ActionItem] = []
    for idx, cm in enumerate(countermeasures[:3]):
        actions.append(
            ActionItem(
                action=cm.description,
                owner=team_names[idx % len(team_names)],
                due_date=date.today() + timedelta(days=14 * (idx + 1)),
                kpi=define_input.goal_metric.metric_name,
                control_method="Weekly control chart + trigger escalation if 2 misses",
                responsible=[team_names[idx % len(team_names)]],
                accountable=accountable,
                consulted=team_names[1:2],
                informed=team_names[2:3],
            )
        )

    control_plan = ControlPlan(
        cadence="Weekly KPI review",
        response_plan="If KPI misses target in two consecutive periods, open rapid containment and re-run 5 Whys",
        standard_work_update="Update SOP, training matrix, and error-proofing checklist",
        audit_frequency="Monthly layered process audit",
    )

    score, notes = confidence_notes_from_data(measure_input.dataset_present, len(root_causes))
    narrative = _build_narrative(define_input, measure_summary, len(root_causes))

    traceability_graph = {
        "root_to_countermeasure": {rc.id: [cm.id for cm in countermeasures if rc.id in cm.linked_root_cause_ids] for rc in root_causes},
        "countermeasure_to_action": {cm.id: [a.action for a in actions if cm.description[:24] in a.action] for cm in countermeasures},
    }

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
        dmaic_narrative=narrative,
        traceability_graph=traceability_graph,
    )
