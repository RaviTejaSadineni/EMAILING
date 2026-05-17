from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResponseTimeStat(BaseModel):
    avg_hours: float
    median_hours: float
    p90_hours: float
    trend: str  # "improving" | "worsening" | "stable"


class EmailVolume(BaseModel):
    sent: int
    received: int
    cc: int
    period: str


class StakeholderPerformance(BaseModel):
    stakeholder_id: str
    name: str | None
    department: str | None
    role: str | None
    response_time: ResponseTimeStat
    email_volumes: list[EmailVolume]
    active_contracts: int
    completed_contracts: int
    sla_breached_contracts: int
    bottleneck_count: int
    avg_delay_caused_hours: float
    sla_breach_rate: float

    model_config = ConfigDict(from_attributes=True)


class ResponseTimeTrendPoint(BaseModel):
    period: str
    avg_hours: float
    median_hours: float


class ResponseTimeTrend(BaseModel):
    stakeholder_id: str
    points: list[ResponseTimeTrendPoint]


class WorkloadPoint(BaseModel):
    period: str
    active_contracts: int


class WorkloadTimeline(BaseModel):
    stakeholder_id: str
    points: list[WorkloadPoint]


class ContractInvolvement(BaseModel):
    contract_id: str
    agreement_name: str | None
    role: str | None
    contribution_score: float
    avg_response_time_hours: float | None
    stage: str | None
    sla_status: str


class CommunicationNode(BaseModel):
    stakeholder_id: str
    name: str | None
    email: str
    department: str | None
    total_interactions: int


class CommunicationEdge(BaseModel):
    source: str
    target: str
    weight: int
    email_count: int


class CommunicationNetwork(BaseModel):
    nodes: list[CommunicationNode]
    edges: list[CommunicationEdge]


class StakeholderComparisonItem(BaseModel):
    stakeholder_id: str
    name: str | None
    department: str | None
    avg_response_time_hours: float
    email_volume: int
    contract_count: int
    sla_breach_rate: float
    bottleneck_frequency: int


class StakeholderComparison(BaseModel):
    items: list[StakeholderComparisonItem]


class DepartmentMember(BaseModel):
    stakeholder_id: str
    name: str | None
    role: str | None


class DepartmentAnalyticsItem(BaseModel):
    department: str
    member_count: int
    avg_response_time_hours: float
    contract_throughput: int
    bottleneck_frequency: int
    efficiency_rank: int


class DepartmentAnalytics(BaseModel):
    items: list[DepartmentAnalyticsItem]


class DepartmentComparison(BaseModel):
    dept1: DepartmentAnalyticsItem
    dept2: DepartmentAnalyticsItem
    winner: str


class StakeholderRanking(BaseModel):
    rank: int
    stakeholder_id: str
    name: str | None
    department: str | None
    metric_value: float
    metric_name: str


class WorkloadBalanceItem(BaseModel):
    stakeholder_id: str
    name: str | None
    department: str | None
    active_contracts: int
    load_category: str  # "overloaded" | "normal" | "underloaded"


class WorkloadBalance(BaseModel):
    items: list[WorkloadBalanceItem]
    avg_load: float
    overloaded_count: int


class AIRecommendation(BaseModel):
    stakeholder_id: str
    recommendations: list[str]
    generated_at: datetime
