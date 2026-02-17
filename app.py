from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from a3_autopilot.dmaic import orchestrate_dmaic
from a3_autopilot.ingestion import load_dataset
from a3_autopilot.models import DefineInput, GoalMetric, MeasureInput, TeamMember
from a3_autopilot.problem_coach import (
    EXAMPLE_PROBLEM_STATEMENT,
    build_define_draft,
    evaluate_problem_statement,
    rewrite_problem_statement,
)
from a3_autopilot.scoring import quality_gate
from a3_autopilot.slide_builder import render_single_slide
from a3_autopilot.utils import model_dump_compat, to_date_or_default


WIDGET_DEFAULTS = {
    "problem_statement_input": "",
    "project_y": "",
    "goal_statement": "",
    "do_not_harm": "",
    "business_impact": "",
    "scope_in": "",
    "scope_out": "",
    "goal_metric": "",
    "target": 0.0,
    "baseline": 0.0,
    "team_raw": "",
}


def _init_state() -> None:
    if "coach_feedback" not in st.session_state:
        st.session_state["coach_feedback"] = None
    if "coached_rewrite" not in st.session_state:
        st.session_state["coached_rewrite"] = ""

    pending = st.session_state.pop("_pending_widget_updates", None)
    if isinstance(pending, dict):
        for key, value in pending.items():
            st.session_state[key] = value

    for key, value in WIDGET_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_app() -> None:
    st.set_page_config(page_title="A3 Autopilot", layout="wide")
    st.title("A3 Autopilot")
    st.caption("A guided DMAIC coach that walks users step-by-step and builds a one-slide A3 export.")

    _init_state()

    st.info(
        "1) Draft a strong problem statement. 2) Ask AI Coach to review and pre-fill Define fields. "
        "3) Update anything you want, then generate the A3 package."
    )

    sections = st.tabs(["A) Define", "B) Measure", "C) Analyze", "D) Improve", "E) Control"])
    with st.form("dmaic_form"):
        with sections[0]:
            st.subheader("Step 1: Define the problem")
            problem_statement = st.text_area(
                "Problem statement *",
                key="problem_statement_input",
                placeholder="Describe the issue with a time period, measurable gap, and impact.",
                height=140,
            )
            st.markdown("**Example**")
            st.caption(EXAMPLE_PROBLEM_STATEMENT)

            project_y = st.text_input("Project Y", key="project_y", placeholder="Primary Y/output this project improves")
            goal_statement = st.text_area("Goal", key="goal_statement", placeholder="SMART goal statement", height=80)
            do_not_harm = st.text_area("Do not harm", key="do_not_harm", placeholder="Guardrails", height=80)
            business_impact = st.text_area("Business impact", key="business_impact", placeholder="Compliance / quality / patient impact", height=90)

            c1, c2 = st.columns(2)
            with c1:
                scope_in = st.text_input("Scope in", key="scope_in", placeholder="Complaint intake through quality review")
                goal_metric = st.text_input("Goal metric", key="goal_metric", placeholder="First-pass complete complaint records (%)")
                target = st.number_input("Target", min_value=0.0, key="target", step=0.5)
            with c2:
                scope_out = st.text_input("Scope out", key="scope_out", placeholder="Post-triage CAPA execution")
                due_date = st.date_input("Due date", value=date.today() + timedelta(days=60))
                baseline = st.number_input("Baseline", min_value=0.0, key="baseline", step=0.5)

            team_raw = st.text_area(
                "Team members (Name:Role per line)",
                key="team_raw",
                placeholder="Jane Smith:Quality Manager\nA. Lee:Complaint Analyst",
            )

        with sections[1]:
            st.subheader("Step 2: Add data (optional but recommended)")
            uploaded = st.file_uploader("Upload CSV/XLSX (optional)", type=["csv", "xlsx"])

        with sections[2]:
            st.subheader("Step 3: Analyze")
            st.markdown("Pareto, fishbone (6M), and 5 Whys are auto-generated.")

        with sections[3]:
            st.subheader("Step 4: Improve")
            st.markdown("Countermeasures are scored on impact/effort/risk with primary and backup recommendations.")

        with sections[4]:
            st.subheader("Step 5: Control")
            st.markdown("Control plan and RACI are auto-generated with owner, due date, KPI, and control method.")

        coach_clicked = st.form_submit_button("Ask AI Coach")
        use_rewrite_clicked = st.form_submit_button("Use coached rewrite")
        submitted = st.form_submit_button("Generate complete DMAIC A3")

    if coach_clicked:
        feedback = evaluate_problem_statement(problem_statement)
        draft = build_define_draft(problem_statement)
        coached_rewrite = rewrite_problem_statement(problem_statement)

        st.session_state["coach_feedback"] = feedback
        st.session_state["coached_rewrite"] = coached_rewrite
        st.session_state["_pending_widget_updates"] = {
            "project_y": draft.project_y,
            "goal_statement": draft.goal_statement,
            "do_not_harm": draft.do_not_harm,
            "business_impact": draft.business_impact,
            "scope_in": draft.scope_in,
            "scope_out": draft.scope_out,
            "goal_metric": draft.goal_metric,
            "baseline": float(draft.baseline),
            "target": float(draft.target),
        }
        st.rerun()

    if use_rewrite_clicked and st.session_state.get("coached_rewrite"):
        st.session_state["_pending_widget_updates"] = {
            "problem_statement_input": st.session_state["coached_rewrite"],
        }
        st.rerun()

    feedback = st.session_state.get("coach_feedback")
    if feedback is not None:
        st.subheader("AI Coach feedback")
        st.metric("Problem statement quality", f"{feedback.score}/100")
        st.caption(f"Detected context: {feedback.detected_context.replace('_', ' ')}")
        if feedback.strengths:
            st.success("Strong components detected")
            st.markdown("\n".join([f"- {item}" for item in feedback.strengths]))
        if feedback.missing_components:
            st.warning("Missing or weak components")
            st.markdown("\n".join([f"- {item}" for item in feedback.missing_components]))
        st.info(f"Suggested rewrite template: {feedback.suggested_rewrite}")
        st.write("**Coached rewrite (based on your draft):**")
        st.text_area(
            "Coached rewrite preview",
            value=st.session_state.get("coached_rewrite") or "",
            height=100,
            disabled=True,
            label_visibility="collapsed",
        )
        st.info("Define fields were pre-filled. Review and edit as needed.")

    if not submitted:
        return

    if not problem_statement.strip():
        st.error("Problem statement is required.")
        return

    team = []
    for line in team_raw.splitlines():
        if ":" in line:
            n, r = line.split(":", 1)
            team.append(TeamMember(name=n.strip(), role=r.strip()))

    define = DefineInput(
        problem_statement=problem_statement.strip(),
        project_y=project_y or None,
        goal_statement=goal_statement or None,
        do_not_harm=do_not_harm or None,
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
    with open(output_pptx, "rb") as f:
        st.download_button(
            "Download one-slide PPTX",
            data=f,
            file_name="a3_autopilot_single_slide.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    with st.expander("Raw package"):
        st.json(
            {
                "define": model_dump_compat(define),
                "measure_summary": pkg.measure_summary,
            }
        )


def _launch_streamlit() -> None:
    from streamlit.web import bootstrap

    bootstrap.run(str(Path(__file__).resolve()), "", [], {})


if __name__ == "__main__":
    from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx

    if get_script_run_ctx() is None:
        _launch_streamlit()
    else:
        render_app()
