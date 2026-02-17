from a3_autopilot.problem_coach import (
    EXAMPLE_PROBLEM_STATEMENT,
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
    assert "Workflow" in draft.project_y or "workflow" in draft.project_y.lower()
