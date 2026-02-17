from a3_autopilot.problem_coach import (
    answer_coaching_question,
    assess_define_section,
    build_define_draft,
    detect_context,
    evaluate_problem_statement,
    generate_lean_tool_guidance,
    rewrite_define_fields,
    rewrite_problem_statement,
)


def test_problem_statement_coach_flags_gaps() -> None:
    feedback = evaluate_problem_statement("Complaint handling is bad.")

    assert feedback.score < 80
    assert any("time frame" in item.lower() for item in feedback.missing_components)


def test_build_define_draft_prefills_fields() -> None:
    draft = build_define_draft("Our process has 30% rework and frequent delays.")

    assert draft.project_y
    assert draft.goal_statement
    assert draft.goal_metric


def test_rewrite_problem_statement_returns_expanded_version() -> None:
    rewritten = rewrite_problem_statement("Complaint intake has 34% missing mandatory fields causing delays.")

    assert "34.0%" in rewritten


def test_general_problem_uses_general_context() -> None:
    statement = "Getting done work around here is difficult and tasks are often delayed."

    assert detect_context(statement) == "general"


def test_assess_define_section_scores_completion() -> None:
    feedback = assess_define_section(
        problem_statement="Our process is slow and causes missed deadlines.",
        project_y="",
        goal_statement="",
        do_not_harm="",
        business_impact="",
        scope_in="",
        scope_out="",
        goal_metric="",
        baseline=0,
        target=0,
    )

    assert feedback.score < 50
    assert feedback.improvements


def test_rewrite_define_fields_includes_filled_inputs() -> None:
    rewrites = rewrite_define_fields(
        {
            "problem_statement": "Our turnaround is slow and causes missed commitments.",
            "project_y": "Turnaround Time",
            "goal_statement": "Reduce cycle time",
            "do_not_harm": "Do not increase defects",
            "business_impact": "Lost productivity",
            "scope_in": "Intake to completion",
            "scope_out": "External vendors",
            "goal_metric": "Cycle time (days)",
        }
    )

    assert "problem_statement" in rewrites
    assert "project_y" in rewrites
    assert "goal_metric" in rewrites


def test_generate_lean_tool_guidance_has_key_tools() -> None:
    tools = generate_lean_tool_guidance("Process delays are hurting delivery.")

    names = [t.tool_name for t in tools]
    assert any("Value Stream" in name for name in names)
    assert any("VOC" in name for name in names)


def test_answer_coaching_question_returns_response() -> None:
    answer = answer_coaching_question("What is VOC?", {"goal_statement": "Improve lead time"})

    assert "VOC" in answer
