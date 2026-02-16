from __future__ import annotations

from datetime import date
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from a3_autopilot.models import DmaicPackage
from a3_autopilot.raci import build_raci


def _add_textbox(slide, left, top, width, height, text, size=10, bold=False, color=None):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.clear()
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    return box


def render_single_slide(pkg: DmaicPackage, output_path: str | Path) -> str:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    top = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.64))
    top.fill.solid()
    top.fill.fore_color.rgb = RGBColor(30, 50, 77)
    top.line.color.rgb = RGBColor(30, 50, 77)

    _add_textbox(
        slide,
        Inches(0.2),
        Inches(0.06),
        Inches(12.9),
        Inches(0.5),
        f"A3 Autopilot DMAIC | Owner: {pkg.define.team[0].name if pkg.define.team else 'TBD'} | Date: {date.today()}\nProblem: {pkg.define.problem_statement}",
        size=11,
        bold=True,
        color=RGBColor(255, 255, 255),
    )

    left_x, mid_x, right_x = Inches(0.2), Inches(4.55), Inches(8.9)
    col_w, top_y, col_h = Inches(4.2), Inches(0.75), Inches(6.15)
    for x, title in [(left_x, "DEFINE + MEASURE"), (mid_x, "ANALYZE"), (right_x, "IMPROVE + CONTROL")]:
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, top_y, col_w, col_h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(245, 247, 250)
        shape.line.color.rgb = RGBColor(200, 205, 210)
        _add_textbox(slide, x + Inches(0.12), top_y + Inches(0.06), Inches(3.9), Inches(0.25), title, size=10, bold=True)

    charter = pkg.measure_summary.get("project_charter", "")
    left_text = (
        f"Charter Goal:\n{charter}\n\n"
        f"Baseline Mean Impact: {pkg.measure_summary.get('baseline_mean_impact', 'N/A')}\n"
        f"Total Impact: {pkg.measure_summary.get('baseline_total_impact', 'N/A')}\n"
        f"Records: {pkg.measure_summary.get('records', 0)}\n"
        f"Vital Few Categories: {pkg.measure_summary.get('vital_few_count', 0)}\n"
        f"Target: {pkg.define.goal_metric.target} by {pkg.define.goal_metric.due_date}"
    )
    _add_textbox(slide, left_x + Inches(0.12), Inches(1.1), Inches(3.92), Inches(1.55), left_text, size=7)
    if pkg.pareto_chart_path and Path(pkg.pareto_chart_path).exists():
        slide.shapes.add_picture(str(pkg.pareto_chart_path), left_x + Inches(0.15), Inches(2.7), width=Inches(3.85), height=Inches(2.2))

    fish_lines = [f"{k}: {v[0][:43]}" for k, v in pkg.fishbone.items()]
    _add_textbox(slide, mid_x + Inches(0.12), Inches(1.1), Inches(3.92), Inches(2.1), "Fishbone (6M):\n" + "\n".join(fish_lines), size=7)
    why_lines = [f"{w.level}. {w.why[:54]} | conf:{w.confidence:.2f}" for w in pkg.five_whys[:5]]
    _add_textbox(slide, mid_x + Inches(0.12), Inches(3.25), Inches(3.92), Inches(1.35), "5 Whys:\n" + "\n".join(why_lines), size=7)
    _add_textbox(
        slide,
        mid_x + Inches(0.12),
        Inches(4.65),
        Inches(3.92),
        Inches(1.95),
        "DMAIC Narrative:\n"
        + "\n".join([f"{k.title()}: {v[:84]}" for k, v in pkg.dmaic_narrative.items()]),
        size=7,
    )

    counter_lines = [
        f"{cm.id} ({'PRIMARY' if cm.is_primary else 'BACKUP' if cm.is_backup else 'ALT'}) score={cm.priority_score}: {cm.description[:36]}"
        for cm in pkg.countermeasures[:3]
    ]
    action_lines = [f"- {a.owner} | {a.due_date} | KPI:{a.kpi}" for a in pkg.actions[:3]]
    _add_textbox(slide, right_x + Inches(0.12), Inches(1.1), Inches(3.92), Inches(2.05), "Countermeasures:\n" + "\n".join(counter_lines), size=7)
    _add_textbox(slide, right_x + Inches(0.12), Inches(3.2), Inches(3.92), Inches(1.2), "Actions:\n" + "\n".join(action_lines), size=7)

    raci = build_raci(pkg.actions)
    raci_lines = [f"{a[:14]}: " + ", ".join([f"{p}:{r}" for p, r in row.items()]) for a, row in list(raci.items())[:2]]
    _add_textbox(slide, right_x + Inches(0.12), Inches(4.45), Inches(3.92), Inches(0.9), "Mini RACI:\n" + "\n".join(raci_lines), size=7)

    cp = pkg.control_plan
    _add_textbox(
        slide,
        right_x + Inches(0.12),
        Inches(5.38),
        Inches(3.92),
        Inches(1.22),
        f"Control Plan:\nCadence: {cp.cadence}\nAudit: {cp.audit_frequency}\nResponse: {cp.response_plan[:52]}",
        size=7,
    )

    assumptions = " | ".join([a.text for a in pkg.assumptions]) or "No major assumptions"
    conf = f"Confidence {pkg.confidence_score:.2f}; improve with: {'; '.join(pkg.confidence_notes) if pkg.confidence_notes else 'more periodic data'}"
    _add_textbox(slide, Inches(0.2), Inches(6.96), Inches(12.9), Inches(0.45), f"{assumptions} || {conf} || Next review: {date.today()}", size=7)

    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    prs.save(output_path)
    return output_path
