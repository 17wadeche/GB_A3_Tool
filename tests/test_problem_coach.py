from a3_autopilot.problem_coach import EXAMPLE_PROBLEM_STATEMENT, evaluate_problem_statement


def test_problem_statement_example_scores_high() -> None:
    feedback = evaluate_problem_statement(EXAMPLE_PROBLEM_STATEMENT)

    assert feedback.score >= 80
    assert not feedback.missing_components


def test_problem_statement_coach_flags_gaps() -> None:
    feedback = evaluate_problem_statement("Complaint handling is bad.")

    assert feedback.score < 80
    assert any("time frame" in item.lower() for item in feedback.missing_components)
    assert any("measurable" in item.lower() for item in feedback.missing_components)
