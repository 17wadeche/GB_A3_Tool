from a3_autopilot.five_whys import generate_five_whys


def test_five_whys_generates_3_to_5_levels():
    whys = generate_five_whys("Defects are high", ["Rework", "Delay", "Handoff"])
    assert 3 <= len(whys) <= 5
    assert all(w.evidence_note for w in whys)
    assert all(0 <= w.confidence <= 1 for w in whys)
