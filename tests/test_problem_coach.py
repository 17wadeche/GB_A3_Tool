from a3_autopilot.problem_coach import (
    EXAMPLE_PROBLEM_STATEMENT,
    assess_define_section,
    build_define_draft,
    detect_context,
    evaluate_problem_statement,
    rewrite_problem_statement,
)


def test_problem_statement_example_scores_high() -> None:
    feedback = evaluate_problem_statement(EXAMPLE_PROBLEM_STATEMENT)

    assert feedback.score >= 80
    assert not feedback.missing_components
    assert feedback.detected_context == "complaint_handling"


def test_problem_statement_coach_flags_gaps() -> None:
    feedback = evaluate_problem_statement("Complaint handling is bad.")

    assert feedback.score < 80
    assert any("time frame" in item.lower() for item in feedback.missing_components)
    assert any("measurable" in item.lower() for item in feedback.missing_components)


def test_build_define_draft_prefills_fields() -> None:
    draft = build_define_draft(EXAMPLE_PROBLEM_STATEMENT)

    assert draft.project_y
    assert draft.goal_statement
    assert draft.do_not_harm
    assert draft.goal_metric
    assert draft.target > 0


def test_rewrite_problem_statement_returns_expanded_version() -> None:
    rewritten = rewrite_problem_statement("Complaint intake has 34% missing mandatory fields causing delays.")

    assert "34.0%" in rewritten
    assert "compliance risk" in rewritten.lower() or "regulatory" in rewritten.lower()


def test_general_problem_uses_general_context() -> None:
    statement = "Getting done work around here is difficult and tasks are often delayed."

    assert detect_context(statement) == "general"
    feedback = evaluate_problem_statement(statement)
    assert feedback.detected_context == "general"
    draft = build_define_draft(statement)
    assert "Process" in draft.project_y or "workflow" in draft.project_y.lower()


def test_a3_problem_prefill_is_a3_specific() -> None:
    statement = (
        "The current A3 process is complex and burdensome, causing extra work and frustration "
        "for coaches and participants. This leads to lower A3 completion rates."
    )
    draft = build_define_draft(statement)

    assert "A3" in draft.project_y
    assert "A3 completion rate" in draft.goal_metric


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
