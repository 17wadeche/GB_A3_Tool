# A3 Autopilot

A production-ready Streamlit app that generates a complete DMAIC A3 package in **Autopilot mode** and exports **exactly one PowerPoint file with exactly one slide**.

## Features

- DMAIC flow enforced in order: **Define → Measure → Analyze → Improve → Control**
- Built-in tools:
  - Project Charter
  - Pareto analysis + chart
  - Fishbone (6M)
  - 5 Whys
  - RACI matrix
- Handles optional CSV/XLSX uploads with messy column names (spaces, case, missing values)
- Best-effort assumptions are labeled as `ASSUMPTION`
- Traceability rules:
  - Countermeasures linked to root causes
  - Actions include owner, due date, KPI, and control method
- Quality gate before export
- One-slide executive PPT output (16:9)

## Repository layout

- `app.py` — Streamlit wizard UI
- `a3_autopilot/`
  - `models.py` — Pydantic schemas
  - `ingestion.py` — file parsing + column normalization
  - `charter.py` — project charter generation
  - `pareto.py` — Pareto table + chart generation
  - `fishbone.py` — 6M fishbone structure
  - `five_whys.py` — 5 Whys + root causes + confidence
  - `raci.py` — RACI builder
  - `dmaic.py` — end-to-end orchestrator + traceability
  - `slide_builder.py` — one-slide PPTX renderer
  - `scoring.py` — quality gate + confidence notes
  - `assumptions.py` — assumption tracking
  - `utils.py` — utility helpers
- `tests/` — pytest unit tests
- `examples/example_input.csv` — sample upload data
- `examples/generate_sample_output.py` — script to generate sample output PPTX

## Run steps

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest -q
```

Generate the sample output artifact:

```bash
python examples/generate_sample_output.py
```

## Notes

- Optional LLM summarization is intentionally interface-ready and can be added behind module boundaries without changing the workflow.
- Export always creates one `.pptx` containing one slide.
- The binary sample PPTX is intentionally generated locally (not committed) to keep PR diffs text-only and compatible with code-review tooling.
