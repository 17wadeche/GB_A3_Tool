from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from a3_autopilot.dmaic import orchestrate_dmaic
from a3_autopilot.ingestion import load_dataset
from a3_autopilot.models import DefineInput, GoalMetric, MeasureInput, TeamMember
from a3_autopilot.problem_coach import coach_define_phase, tool_guidance_from_result
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
        "coach_result": None,
        "prefill_notes": [],
        "coach_error": "",
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
    st.caption("Black Belt-style DMAIC coach with AI-powered Define coaching and Lean Six Sigma tool guidance.")
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

            team_raw = st.text_area("Team members (Name:Role per line)", key="team_raw", placeholder="Name:Role")

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
            st.markdown("Ask anything about VOC, CTQ, SIPOC, process mapping, VSM, MSA, capability, and control planning.")
            question = st.text_input("Coaching question (optional)", key="coach_question")

        coach_clicked = st.form_submit_button("Ask AI Coach")
        submitted = st.form_submit_button("Generate complete DMAIC A3")

    if coach_clicked:
        define_fields = {
            "problem_statement": problem_statement,
            "project_y": project_y,
            "goal_statement": goal_statement,
            "do_not_harm": do_not_harm,
            "business_impact": business_impact,
            "scope_in": scope_in,
            "scope_out": scope_out,
            "goal_metric": goal_metric,
            "baseline": baseline,
            "target": target,
            "due_date": str(due_date),
        }
        try:
            result = coach_define_phase(problem_statement, define_fields, question=question)
            st.session_state["coach_result"] = result
            st.session_state["coach_error"] = ""

            updates = {}
            notes: list[str] = []
            proposed = result.get("proposed_fields", {}) or {}
            for key in ["project_y", "goal_statement", "do_not_harm", "business_impact", "scope_in", "scope_out", "goal_metric"]:
                if _text_empty(str(define_fields.get(key, ""))) and proposed.get(key):
                    updates[key] = str(proposed[key])
                    notes.append(f"Filled {key.replace('_', ' ').title()} from AI.")

            if baseline <= 0 and proposed.get("baseline"):
                try:
                    updates["baseline"] = float(proposed["baseline"])
                    notes.append("Filled Baseline from AI.")
                except (TypeError, ValueError):
                    pass
            if target <= 0 and proposed.get("target"):
                try:
                    updates["target"] = float(proposed["target"])
                    notes.append("Filled Target from AI.")
                except (TypeError, ValueError):
                    pass

            st.session_state["prefill_notes"] = notes
            if updates:
                st.session_state["_pending_widget_updates"] = updates
                st.rerun()
        except RuntimeError as exc:
            st.session_state["coach_error"] = str(exc)

    if st.session_state.get("coach_error"):
        st.error(st.session_state["coach_error"])

    result = st.session_state.get("coach_result")
    if isinstance(result, dict):
        pf = result.get("problem_feedback", {}) or {}
        df = result.get("define_feedback", {}) or {}
        rewrites = result.get("rewrites", {}) or {}

        st.subheader("AI Coach feedback")
        c1, c2 = st.columns(2)
        c1.metric("Problem statement quality", f"{pf.get('score', 0)}/100")
        c2.metric("Define section quality", f"{df.get('score', 0)}/100")

        strengths = pf.get("strengths", []) or []
        missing = pf.get("missing_components", []) or []
        if strengths:
            st.success("Problem statement strengths")
            st.markdown("\n".join([f"- {item}" for item in strengths]))
        if missing:
            st.warning("Problem statement improvements")
            st.markdown("\n".join([f"- {item}" for item in missing]))

        define_improvements = df.get("improvements", []) or []
        if define_improvements:
            st.warning("Define field improvements")
            st.markdown("\n".join([f"- {item}" for item in define_improvements]))

        st.info(f"Suggested problem statement template: {pf.get('suggested_rewrite', '')}")
        st.write("**Coached rewrites for all currently filled Define fields**")
        for field_name, rewrite in rewrites.items():
            st.markdown(f"**{field_name.replace('_', ' ').title()}**")
            st.caption(str(rewrite))

        notes = st.session_state.get("prefill_notes") or []
        if notes:
            st.info("Only empty fields were auto-filled:\n" + "\n".join([f"- {n}" for n in notes]))
        else:
            st.info("No fields were overwritten.")

        tools = tool_guidance_from_result(result)
        if tools:
            st.subheader("Black Belt Lean Six Sigma tool guidance")
            for item in tools:
                with st.expander(item.tool_name):
                    st.write(f"**When to use:** {item.when_to_use}")
                    st.write(f"**Expected output:** {item.output_expected}")
                    st.write(f"**Coach prompt:** {item.starter_prompt}")

        answer = result.get("answer", "")
        if answer:
            st.success(answer)

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
