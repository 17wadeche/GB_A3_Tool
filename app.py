from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from a3_autopilot.dmaic import orchestrate_dmaic
from a3_autopilot.ingestion import load_dataset
from a3_autopilot.models import DefineInput, GoalMetric, MeasureInput, TeamMember
from a3_autopilot.scoring import quality_gate
from a3_autopilot.slide_builder import render_single_slide
from a3_autopilot.utils import model_dump_compat, to_date_or_default


st.set_page_config(page_title="A3 Autopilot", layout="wide")
st.title("A3 Autopilot")
st.caption("Autopilot default: minimal inputs, inferred assumptions labeled ASSUMPTION, one-slide export.")

sections = st.tabs(["A) Define", "B) Measure", "C) Analyze", "D) Improve", "E) Control"])

with st.form("dmaic_form"):
    with sections[0]:
        problem_statement = st.text_input("Problem statement *", placeholder="Late delivery defects exceed target")
        business_impact = st.text_input("Business impact")
        c1, c2 = st.columns(2)
        with c1:
            scope_in = st.text_input("Scope in", value="Order-to-ship")
            goal_metric = st.text_input("Goal metric", value="Defect rate")
            target = st.number_input("Target", min_value=0.0, value=5.0, step=0.5)
        with c2:
            scope_out = st.text_input("Scope out", value="Supplier lead-time")
            due_date = st.date_input("Due date", value=date.today() + timedelta(days=60))
            baseline = st.number_input("Baseline", min_value=0.0, value=12.0, step=0.5)
        team_raw = st.text_area("Team members (Name:Role per line)", value="Alex:Champion\nPriya:Process Owner\nSam:Analyst")

    with sections[1]:
        uploaded = st.file_uploader("Upload CSV/XLSX (optional)", type=["csv", "xlsx"])
        st.caption("Field mapping helper appears after upload.")

    with sections[2]:
        st.markdown("Pareto, fishbone (6M), and 5 Whys are auto-generated.")
    with sections[3]:
        st.markdown("Countermeasures are scored on impact/effort/risk with primary + backup recommendation.")
    with sections[4]:
        st.markdown("Control plan + RACI are auto-generated with owner, due date, KPI, and control method.")

    submitted = st.form_submit_button("Generate complete DMAIC A3")

if submitted:
    if not problem_statement.strip():
        st.error("Problem statement is required.")
        st.stop()

    team = []
    for line in team_raw.splitlines():
        if ":" in line:
            n, r = line.split(":", 1)
            team.append(TeamMember(name=n.strip(), role=r.strip()))

    define = DefineInput(
        problem_statement=problem_statement.strip(),
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
        dataset, auto_mapping = load_dataset(uploaded)
        st.success(f"Loaded {len(dataset)} rows.")
        st.write("Auto-detected mapping:", auto_mapping)

        cols = ["(none)"] + list(dataset.columns)
        field_map = {}
        for canonical in ["category", "impact", "date", "process_step", "owner"]:
            default = auto_mapping.get(canonical, "(none)")
            index = cols.index(default) if default in cols else 0
            selected = st.selectbox(f"Map '{canonical}'", cols, index=index)
            if selected != "(none)":
                field_map[canonical] = selected
        mapping = field_map

    measure = MeasureInput(dataset_present=dataset is not None, field_mapping=mapping)
    pkg = orchestrate_dmaic(define_input=define, measure_input=measure, dataset=dataset, output_dir="examples")

    passed, issues = quality_gate(pkg)
    st.subheader("Quality Gate")
    if passed:
        st.success("PASS: export requirements met.")
    else:
        st.error(f"FAIL: {issues}")

    output_pptx = render_single_slide(pkg, Path("examples") / "sample_a3_single_slide.pptx")

    st.subheader("Autopilot Results")
    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence", f"{pkg.confidence_score:.2f}")
    c2.metric("Root causes", len(pkg.root_causes))
    c3.metric("Countermeasures", len(pkg.countermeasures))

    st.write("**Assumptions**", [a.text for a in pkg.assumptions] or ["None"])
    st.write("**Confidence improvement data needed**", pkg.confidence_notes)
    st.write("**Primary countermeasure**", [c.description for c in pkg.countermeasures if c.is_primary][:1])
    st.write("**Backup countermeasure**", [c.description for c in pkg.countermeasures if c.is_backup][:1])

    with open(output_pptx, "rb") as f:
        st.download_button(
            "Download one-slide PPTX",
            data=f,
            file_name="a3_autopilot_single_slide.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    if pkg.pareto_chart_path:
        st.image(pkg.pareto_chart_path, caption="Pareto chart")

    with st.expander("DMAIC narrative"):
        st.json(pkg.dmaic_narrative)

    with st.expander("Traceability graph"):
        st.json(pkg.traceability_graph)

    with st.expander("Raw package"):
        st.json(
            {
                "define": model_dump_compat(define),
                "measure_summary": pkg.measure_summary,
                "countermeasures": [model_dump_compat(c) for c in pkg.countermeasures],
                "actions": [model_dump_compat(a) for a in pkg.actions],
            }
        )
