from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from a3_autopilot.dmaic import orchestrate_dmaic
from a3_autopilot.ingestion import load_dataset
from a3_autopilot.models import DefineInput, GoalMetric, MeasureInput, TeamMember
from a3_autopilot.problem_coach import (
    answer_coaching_question,
    assess_define_section,
    build_define_draft,
    evaluate_problem_statement,
    generate_lean_tool_guidance,
    rewrite_define_fields,
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
    "coach_question": "",
}


def _init_state() -> None:
    for key, default in {
        "coach_feedback": None,
        "define_feedback": None,
        "coached_rewrites": {},
        "prefill_notes": [],
        "tool_guidance": [],
        "coach_answer": "",
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    pending = st.session_state.pop("_pending_widget_updates", None)
    if isinstance(pending, dict):
        for key, value in pending.items():
            st.session_state[key] = value

    for key, value in WIDGET_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _text_empty(value: str) -> bool:
    return not (value or "").strip()


def render_app() -> None:
    st.set_page_config(page_title="A3 Autopilot", layout="wide")
    st.title("A3 Autopilot")
    st.caption("Black Belt-style DMAIC coach with advanced Lean Six Sigma tooling support.")
    _init_state()

    sections = st.tabs(["A) Define", "B) Measure", "C) Analyze", "D) Improve", "E) Control", "F) Lean Tool Coach"])
    with st.form("dmaic_form"):
        with sections[0]:
            st.subheader("Define")
            problem_statement = st.text_area(
                "Problem statement *",
                key="problem_statement_input",
                placeholder="State the issue, measurable gap, timeframe, and business impact.",
                height=140,
            )

            project_y = st.text_input("Project Y", key="project_y", placeholder="Primary output variable")
            goal_statement = st.text_area("Goal", key="goal_statement", placeholder="SMART goal statement", height=80)
            do_not_harm = st.text_area("Do not harm", key="do_not_harm", placeholder="Guardrails / constraints", height=80)
            business_impact = st.text_area("Business impact", key="business_impact", placeholder="Business case for improvement", height=90)

            c1, c2 = st.columns(2)
            with c1:
                scope_in = st.text_input("Scope in", key="scope_in", placeholder="What is in scope")
                goal_metric = st.text_input("Goal metric", key="goal_metric", placeholder="Primary CTQ / KPI")
                target = st.number_input("Target", min_value=0.0, key="target", step=0.5)
            with c2:
                scope_out = st.text_input("Scope out", key="scope_out", placeholder="What is out of scope")
                due_date = st.date_input("Due date", value=date.today() + timedelta(days=60))
                baseline = st.number_input("Baseline", min_value=0.0, key="baseline", step=0.5)

            team_raw = st.text_area(
                "Team members (Name:Role per line)",
                key="team_raw",
                placeholder="Name:Role",
            )

        with sections[1]:
            st.subheader("Measure")
            uploaded = st.file_uploader("Upload CSV/XLSX (optional)", type=["csv", "xlsx"])

        with sections[2]:
            st.subheader("Analyze")
            st.markdown("Pareto, fishbone (6M), and 5 Whys are auto-generated from inputs.")

        with sections[3]:
            st.subheader("Improve")
            st.markdown("Countermeasures are scored on impact/effort/risk.")

        with sections[4]:
            st.subheader("Control")
            st.markdown("Control plan and RACI are generated with owner, KPI, and response plan.")

        with sections[5]:
            st.subheader("Lean Tool Coach")
            st.markdown("Use this to guide advanced LSS tools: VOC, CTQ, SIPOC, VSM, process mapping, MSA, capability, and control plans.")

        coach_clicked = st.form_submit_button("Ask AI Coach")
        submitted = st.form_submit_button("Generate complete DMAIC A3")

    if coach_clicked:
        feedback = evaluate_problem_statement(problem_statement)
        define_feedback = assess_define_section(
            problem_statement,
            project_y,
            goal_statement,
            do_not_harm,
            business_impact,
            scope_in,
            scope_out,
            goal_metric,
            baseline,
            target,
        )
        draft = build_define_draft(problem_statement)
        rewrites = rewrite_define_fields(
            {
                "problem_statement": problem_statement,
                "project_y": project_y,
                "goal_statement": goal_statement,
                "do_not_harm": do_not_harm,
                "business_impact": business_impact,
                "scope_in": scope_in,
                "scope_out": scope_out,
                "goal_metric": goal_metric,
            }
        )

        updates: dict[str, str | float] = {}
        notes: list[str] = []
        if _text_empty(problem_statement) and rewrites.get("problem_statement"):
            updates["problem_statement_input"] = rewrites["problem_statement"]
            notes.append("Filled Problem statement from AI coaching rewrite.")
        if _text_empty(project_y):
            updates["project_y"] = draft.project_y
            notes.append("Filled Project Y.")
        if _text_empty(goal_statement):
            updates["goal_statement"] = draft.goal_statement
            notes.append("Filled Goal statement.")
        if _text_empty(do_not_harm):
            updates["do_not_harm"] = draft.do_not_harm
            notes.append("Filled Do not harm.")
        if _text_empty(business_impact):
            updates["business_impact"] = draft.business_impact
            notes.append("Filled Business impact.")
        if _text_empty(scope_in):
            updates["scope_in"] = draft.scope_in
            notes.append("Filled Scope in.")
        if _text_empty(scope_out):
            updates["scope_out"] = draft.scope_out
            notes.append("Filled Scope out.")
        if _text_empty(goal_metric):
            updates["goal_metric"] = draft.goal_metric
            notes.append("Filled Goal metric.")
        if baseline <= 0:
            updates["baseline"] = float(draft.baseline)
            notes.append("Filled Baseline.")
        if target <= 0:
            updates["target"] = float(draft.target)
            notes.append("Filled Target.")

        st.session_state["coach_feedback"] = feedback
        st.session_state["define_feedback"] = define_feedback
        st.session_state["coached_rewrites"] = rewrites
        st.session_state["prefill_notes"] = notes
        st.session_state["tool_guidance"] = generate_lean_tool_guidance(problem_statement)

        if updates:
            st.session_state["_pending_widget_updates"] = updates
            st.rerun()

    feedback = st.session_state.get("coach_feedback")
    define_feedback = st.session_state.get("define_feedback")
    rewrites = st.session_state.get("coached_rewrites") or {}

    if feedback is not None:
        st.subheader("AI Coach feedback")
        c1, c2 = st.columns(2)
        c1.metric("Problem statement quality", f"{feedback.score}/100")
        c2.metric("Define section quality", f"{define_feedback.score}/100" if define_feedback else "N/A")

        if feedback.strengths:
            st.success("Problem statement strengths")
            st.markdown("\n".join([f"- {item}" for item in feedback.strengths]))
        if feedback.missing_components:
            st.warning("Problem statement improvements")
            st.markdown("\n".join([f"- {item}" for item in feedback.missing_components]))

        if define_feedback and define_feedback.improvements:
            st.warning("Define field improvements")
            st.markdown("\n".join([f"- {item}" for item in define_feedback.improvements]))

        st.info(f"Suggested problem statement template: {feedback.suggested_rewrite}")

        st.write("**Coached rewrites for all currently filled Define fields**")
        for field_name, rewrite in rewrites.items():
            st.markdown(f"**{field_name.replace('_', ' ').title()}**")
            st.caption(rewrite)

        notes = st.session_state.get("prefill_notes") or []
        if notes:
            st.info("Only empty fields were auto-filled:\n" + "\n".join([f"- {n}" for n in notes]))
        else:
            st.info("No fields were overwritten.")

        st.subheader("Ask a follow-up coaching question")
        qcol1, qcol2 = st.columns([4, 1])
        with qcol1:
            question = st.text_input("Ask about any Define content or Lean Six Sigma tool", key="coach_question")
        with qcol2:
            asked = st.button("Ask")
        if asked:
            st.session_state["coach_answer"] = answer_coaching_question(
                question,
                {
                    "problem_statement": problem_statement,
                    "project_y": project_y,
                    "goal_statement": goal_statement,
                    "goal_metric": goal_metric,
                },
            )
        if st.session_state.get("coach_answer"):
            st.success(st.session_state["coach_answer"])

        guidance = st.session_state.get("tool_guidance") or []
        if guidance:
            st.subheader("Black Belt Lean Six Sigma tool guidance")
            for item in guidance:
                with st.expander(item.tool_name):
                    st.write(f"**When to use:** {item.when_to_use}")
                    st.write(f"**Expected output:** {item.output_expected}")
                    st.write(f"**Coach prompt:** {item.starter_prompt}")

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
    st.success("PASS: export requirements met.") if passed else st.error(f"FAIL: {issues}")

    output_pptx = render_single_slide(pkg, Path("examples") / "sample_a3_single_slide.pptx")
    with open(output_pptx, "rb") as f:
        st.download_button(
            "Download one-slide PPTX",
            data=f,
            file_name="a3_autopilot_single_slide.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    with st.expander("Raw package"):
        st.json({"define": model_dump_compat(define), "measure_summary": pkg.measure_summary})


def _launch_streamlit() -> None:
    from streamlit.web import bootstrap

    bootstrap.run(str(Path(__file__).resolve()), "", [], {})


if __name__ == "__main__":
    from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx

    if get_script_run_ctx() is None:
        _launch_streamlit()
    else:
        render_app()
