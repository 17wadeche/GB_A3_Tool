import pandas as pd
from a3_autopilot.pareto import build_pareto
def test_pareto_vital_few_and_cumulative():
    df = pd.DataFrame(
        {
            "category": ["A", "A", "B", "C"],
            "impact": [50, 10, 20, 20],
        }
    )
    p = build_pareto(df, "category", "impact")
    assert p.iloc[0]["category"] == "A"
    assert p.iloc[-1]["cumulative_pct"] == 100
    assert p["vital_few"].any()