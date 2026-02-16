from __future__ import annotations

from a3_autopilot.models import Assumption


def add_assumption(assumptions: list[Assumption], text: str, reason: str) -> None:
    assumptions.append(Assumption(text=f"ASSUMPTION: {text}", reason=reason))
