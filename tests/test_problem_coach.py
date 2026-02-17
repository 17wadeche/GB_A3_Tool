from a3_autopilot.problem_coach import api_key_available, coach_define_phase, tool_guidance_from_result


def test_tool_guidance_from_result_parses_items() -> None:
    result = {
        "tool_guidance": [
            {
                "tool_name": "VOC + CTQ",
                "when_to_use": "Define",
                "output_expected": "CTQs",
                "starter_prompt": "Build CTQ tree",
            }
        ]
    }
    tools = tool_guidance_from_result(result)
    assert len(tools) == 1
    assert tools[0].tool_name == "VOC + CTQ"


def test_coach_define_phase_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        coach_define_phase("Problem", {"project_y": ""})
        assert False, "Expected RuntimeError when OPENAI_API_KEY is missing"
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)


def test_api_key_available(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert not api_key_available("")
    assert api_key_available("abc")
