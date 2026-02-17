from __future__ import annotations
from collections import defaultdict
from a3_autopilot.models import RootCause
CATEGORIES = ["Man", "Machine", "Method", "Material", "Measurement", "Environment"]
def build_fishbone(problem_statement: str, root_causes: list[RootCause]) -> dict[str, list[str]]:
    fishbone = defaultdict(list)
    for category in CATEGORIES:
        fishbone[category] = []
    for rc in root_causes:
        bucket = rc.category if rc.category in CATEGORIES else "Method"
        fishbone[bucket].append(rc.statement)
    for category in CATEGORIES:
        if not fishbone[category]:
            fishbone[category].append(f"No direct signal yet for {category.lower()} ({problem_statement[:30]}...)")
    return dict(fishbone)
