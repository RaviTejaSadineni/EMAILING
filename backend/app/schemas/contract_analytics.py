from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContractTimelineEvent(BaseModel):
    date: datetime | None
    event_type: str
    stage: str | None
    actor: str | None
    description: str
    email_id: str | None = None


class ContractTimeline(BaseModel):
    contract_id: str
    events: list[ContractTimelineEvent]


class StageDuration(BaseModel):
    stage: str
    duration_hours: float
    entered_at: datetime | None
    exited_at: datetime | None
    actors_involved: list[str]
    emails_in_stage: int
    is_bottleneck: bool


class LifecycleStory(BaseModel):
    contract_id: str
    narrative: str
    generated_at: datetime


class StageDurationStats(BaseModel):
    stage: str
    avg_hours: float
    min_hours: float
    max_hours: float
    median_hours: float
    p90_hours: float
    sample_count: int


class BottleneckReport(BaseModel):
    stage: str
    frequency: int
    avg_delay_hours: float
    top_offenders: list[str]
    bottleneck_score: float


class SLABreachItem(BaseModel):
    contract_id: str
    agreement_name: str | None
    total_cycle_days: float
    breach_days: float
    primary_bottleneck_stage: str | None
    responsible_stakeholders: list[str]


class SLABreachReport(BaseModel):
    total_breaches: int
    items: list[SLABreachItem]


class SLACompliancePeriod(BaseModel):
    period: str
    total: int
    on_track: int
    breached: int
    compliance_rate: float


class SLAComplianceTrend(BaseModel):
    periods: list[SLACompliancePeriod]


class StageTransition(BaseModel):
    from_stage: str
    to_stage: str
    count: int
    avg_duration_hours: float


class NegotiationAnalysis(BaseModel):
    avg_rounds: float
    most_negotiated_clauses: list[dict]
    top_contracts_by_rounds: list[dict]
    correlation_rounds_cycle_time: float | None


class CycleTimeBin(BaseModel):
    label: str
    min_days: float
    max_days: float
    count: int


class CycleTimeDistribution(BaseModel):
    bins: list[CycleTimeBin]
    avg_days: float
    median_days: float


class VelocityPoint(BaseModel):
    period: str
    completed_count: int
    started_count: int


class VelocityTrend(BaseModel):
    points: list[VelocityPoint]


class StageHealthItem(BaseModel):
    stage: str
    contract_count: int
    white_count: int
    yellow_count: int
    red_count: int
    avg_days_in_stage: float


class StageHealth(BaseModel):
    items: list[StageHealthItem]
    as_of: datetime

    model_config = ConfigDict(from_attributes=True)
