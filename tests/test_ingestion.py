import pandas as pd
from a3_autopilot.ingestion import load_dataset
def test_ingestion_normalizes_columns(tmp_path):
    path = tmp_path / "messy.csv"
    df = pd.DataFrame({" Category ": ["A", "B"], " Defect Count ": [2, 3]})
    df.to_csv(path, index=False)
    loaded, mapping = load_dataset(path)
    assert "category" in loaded.columns
    assert "defect_count" in loaded.columns
    assert mapping["category"] == "category"
    assert mapping["impact"] == "defect_count"