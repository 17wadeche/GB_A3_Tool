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

    slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.6)).fill.solid()
    _add_textbox(
        slide,
        Inches(0.2),
        Inches(0.08),
        Inches(12.8),
        Inches(0.45),
        f"A3 Autopilot DMAIC | Owner: {pkg.define.team[0].name if pkg.define.team else 'TBD'} | Date: {date.today()}\nProblem: {pkg.define.problem_statement}",
        size=12,
        bold=True,
        color=RGBColor(255, 255, 255),
    )

    left_x, mid_x, right_x = Inches(0.2), Inches(4.55), Inches(8.9)
    col_w, top_y, col_h = Inches(4.2), Inches(0.75), Inches(6.35)

    for x, title in [(left_x, "DEFINE + MEASURE"), (mid_x, "ANALYZE"), (right_x, "IMPROVE + CONTROL")]:
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, top_y, col_w, col_h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(245, 247, 250)
        shape.line.color.rgb = RGBColor(200, 205, 210)
        _add_textbox(slide, x + Inches(0.1), top_y + Inches(0.05), Inches(3.8), Inches(0.3), title, size=11, bold=True)

    # Left content
    charter = pkg.measure_summary.get("project_charter", "")
    metrics = f"Baseline: {pkg.measure_summary.get('baseline_mean_impact', 'N/A')} | Records: {pkg.measure_summary.get('records', 0)}\nTarget: {pkg.define.goal_metric.target} by {pkg.define.goal_metric.due_date}"
    _add_textbox(slide, left_x + Inches(0.1), Inches(1.15), Inches(3.9), Inches(1.2), f"Charter:\n{charter}\n\n{metrics}", size=8)

    if pkg.pareto_chart_path and Path(pkg.pareto_chart_path).exists():
        slide.shapes.add_picture(str(pkg.pareto_chart_path), left_x + Inches(0.1), Inches(2.45), width=Inches(3.9), height=Inches(2.15))

    # middle analyze content
    fish_lines = []
    for cat, causes in pkg.fishbone.items():
        fish_lines.append(f"{cat}: {causes[0][:40]}")
    _add_textbox(slide, mid_x + Inches(0.1), Inches(1.15), Inches(3.9), Inches(2.25), "Fishbone 6M:\n" + "\n".join(fish_lines), size=8)

    why_lines = [f"{w.level}. {w.why[:58]} ({w.confidence:.2f})" for w in pkg.five_whys[:5]]
    _add_textbox(slide, mid_x + Inches(0.1), Inches(3.55), Inches(3.9), Inches(2.7), "5 Whys:\n" + "\n".join(why_lines), size=8)

    # right content
    action_lines = [f"- {a.action[:40]} | {a.owner} | {a.due_date}" for a in pkg.actions[:3]]
    _add_textbox(slide, right_x + Inches(0.1), Inches(1.15), Inches(3.9), Inches(2.4), "Actions:\n" + "\n".join(action_lines), size=8)

    raci = build_raci(pkg.actions)
    raci_lines = []
    for act, row in list(raci.items())[:2]:
        raci_lines.append(f"{act[:20]}: " + ", ".join([f"{k}:{v}" for k, v in row.items()]))
    _add_textbox(
        slide,
        right_x + Inches(0.1),
        Inches(3.65),
        Inches(3.9),
        Inches(1.2),
        "Mini RACI:\n" + "\n".join(raci_lines),
        size=8,
    )
    cp = pkg.control_plan
    _add_textbox(
        slide,
        right_x + Inches(0.1),
        Inches(4.9),
        Inches(3.9),
        Inches(1.35),
        f"KPI cadence: {cp.cadence}\nResponse: {cp.response_plan[:65]}\nAudit: {cp.audit_frequency}",
        size=8,
    )

    assumption_txt = " | ".join([a.text for a in pkg.assumptions]) or "No major assumptions"
    conf_txt = f"Confidence: {pkg.confidence_score:.2f}; Improve with: {'; '.join(pkg.confidence_notes) if pkg.confidence_notes else 'additional longitudinal data'}"
    _add_textbox(slide, Inches(0.2), Inches(7.0), Inches(12.9), Inches(0.45), f"{assumption_txt} || {conf_txt} || Next review: {date.today()}", size=8)

    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    prs.save(output_path)
    return output_path
