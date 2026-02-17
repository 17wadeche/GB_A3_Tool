from __future__ import annotations
from collections import defaultdict
from a3_autopilot.models import ActionItem
def build_raci(actions: list[ActionItem]) -> dict[str, dict[str, str]]:
    matrix: dict[str, dict[str, str]] = {}
    for action in actions:
        row = defaultdict(str)
        for name in action.responsible:
            row[name] = "R"
        row[action.accountable] = "A"
        for name in action.consulted:
            if not row[name]:
                row[name] = "C"
        for name in action.informed:
            if not row[name]:
                row[name] = "I"
        matrix[action.action] = dict(row)
    return matrix
