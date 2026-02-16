from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from a3_autopilot.dmaic import orchestrate_dmaic
from a3_autopilot.ingestion import load_dataset
from a3_autopilot.models import DefineInput, GoalMetric, MeasureInput, TeamMember
from a3_autopilot.scoring import quality_gate
from a3_autopilot.slide_builder import render_single_slide
from a3_autopilot.utils import to_date_or_default


st.set_page_config(page_title="A3 Autopilot", layout="wide")
st.title("A3 Autopilot")
st.caption("Autopilot mode is default: minimal questions, best-effort assumptions, one-slide PPT output.")

with st.form("define_form"):
    st.subheader("A) Define")
    problem_statement = st.text_input("Problem statement *", placeholder="Example: Late delivery defects exceed target")
    business_impact = st.text_input("Business impact (optional)")
    c1, c2 = st.columns(2)
    with c1:
        scope_in = st.text_input("Scope in", value="Order-to-ship process")
        goal_metric = st.text_input("Goal metric", value="Defect rate")
        target = st.number_input("Target", value=5.0)
    with c2:
        scope_out = st.text_input("Scope out", value="Supplier lead-time changes")
        due_date = st.date_input("Due date", value=date.today() + timedelta(days=60))
        baseline = st.number_input("Baseline (optional)", value=12.0)

    st.markdown("Team members")
    team_raw = st.text_area("Name:Role per line", value="Alex:Champion\nPriya:Process Owner\nSam:Analyst")

    st.subheader("B) Measure")
    uploaded = st.file_uploader("Upload CSV/XLSX (optional)", type=["csv", "xlsx"])
    submitted = st.form_submit_button("Generate DMAIC A3")

if submitted:
    if not problem_statement.strip():
        st.error("Problem statement is required")
        st.stop()

    team = []
    for line in team_raw.splitlines():
        if ":" in line:
            n, r = line.split(":", 1)
            team.append(TeamMember(name=n.strip(), role=r.strip()))

    define = DefineInput(
        problem_statement=problem_statement,
        business_impact=business_impact or None,
        scope_in=scope_in,
        scope_out=scope_out,
        goal_metric=GoalMetric(
            metric_name=goal_metric,
            baseline=baseline,
            target=target,
            due_date=to_date_or_default(str(due_date), date.today() + timedelta(days=60)),
        ),
        team=team,
    )

    dataset = None
    mapping = {}
    if uploaded is not None:
        dataset, mapping = load_dataset(uploaded)
        st.success(f"Loaded {len(dataset)} rows. Auto-mapping: {mapping}")

    measure = MeasureInput(dataset_present=dataset is not None, field_mapping=mapping)
    pkg = orchestrate_dmaic(define, measure, dataset, output_dir="examples")

    passed, issues = quality_gate(pkg)
    st.subheader("Quality gate")
    if passed:
        st.success("Passed")
    else:
        st.error(f"Failed: {issues}")

    output_pptx = render_single_slide(pkg, Path("examples") / "sample_a3_single_slide.pptx")

    st.subheader("Autopilot output")
    st.write(f"Confidence score: {pkg.confidence_score}")
    st.write("Confidence improvement inputs:", pkg.confidence_notes)
    st.write("Assumptions:", [a.text for a in pkg.assumptions])

    with open(output_pptx, "rb") as f:
        st.download_button(
            label="Download one-slide A3 PowerPoint",
            data=f,
            file_name="a3_autopilot_single_slide.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    if pkg.pareto_chart_path:
        st.image(pkg.pareto_chart_path, caption="Pareto chart")

    st.json(
        {
            "define": define.model_dump(mode="json"),
            "measure_summary": pkg.measure_summary,
            "top_countermeasures": [cm.model_dump() for cm in pkg.countermeasures[:3]],
        }
    )
