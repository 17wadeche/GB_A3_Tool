from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Assumption(BaseModel):
    text: str
    reason: str


class TeamMember(BaseModel):
    name: str
    role: str


class GoalMetric(BaseModel):
    metric_name: str
    baseline: Optional[float] = None
    target: float
    due_date: date


class DefineInput(BaseModel):
    problem_statement: str
    business_impact: Optional[str] = None
    scope_in: str
    scope_out: str
    goal_metric: GoalMetric
    team: List[TeamMember]


class MeasureInput(BaseModel):
    dataset_present: bool = False
    field_mapping: Dict[str, str] = Field(default_factory=dict)


class RootCause(BaseModel):
    id: str
    category: str
    statement: str
    evidence_note: str
    confidence: float


class FiveWhyNode(BaseModel):
    level: int
    why: str
    evidence_note: str
    confidence: float


class Countermeasure(BaseModel):
    id: str
    description: str
    linked_root_cause_ids: List[str]
    impact: int
    effort: int
    risk: int


class ActionItem(BaseModel):
    action: str
    owner: str
    due_date: date
    kpi: str
    control_method: str
    responsible: List[str]
    accountable: str
    consulted: List[str] = Field(default_factory=list)
    informed: List[str] = Field(default_factory=list)

    @field_validator("responsible")
    @classmethod
    def responsible_required(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one responsible person is required")
        return v


class ControlPlan(BaseModel):
    cadence: str
    response_plan: str
    standard_work_update: str
    audit_frequency: str


class DmaicPackage(BaseModel):
    define: DefineInput
    measure_summary: Dict[str, float | str]
    pareto_rows: List[Dict[str, float | str]]
    pareto_chart_path: Optional[str] = None
    fishbone: Dict[str, List[str]]
    five_whys: List[FiveWhyNode]
    root_causes: List[RootCause]
    countermeasures: List[Countermeasure]
    actions: List[ActionItem]
    control_plan: ControlPlan
    assumptions: List[Assumption]
    confidence_score: float
    confidence_notes: List[str]
