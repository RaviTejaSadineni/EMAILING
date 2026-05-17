from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardFilters(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    contract_type: str | None = None
    department: str | None = None
    stakeholder_id: str | None = None
    category: str | None = None


class DashboardKPIs(BaseModel):
    total_contracts: int
    active_contracts: int
    completed_contracts: int
    stalled_contracts: int
    total_emails: int
    avg_cycle_time_days: float
    sla_breach_rate: float
    active_negotiations: int
    total_stakeholders: int
    emails_this_week: int
    emails_this_month: int
    most_active_contract_type: str | None
    avg_risk_score: float
    ai_insights_count: int


class TrendDataPoint(BaseModel):
    period: str
    value: float
    count: int


class TrendResponse(BaseModel):
    data: list[TrendDataPoint]
    period: str
    date_from: datetime | None
    date_to: datetime | None


class DistributionItem(BaseModel):
    label: str
    count: int
    percentage: float


class DistributionResponse(BaseModel):
    items: list[DistributionItem]
    total: int


class TopContract(BaseModel):
    contract_id: str
    agreement_name: str | None
    counterparty_name: str | None
    current_stage: str | None
    days_stalled: float
    risk_score: float | None
    sla_breached: bool


class TopStakeholder(BaseModel):
    stakeholder_id: str
    name: str | None
    department: str | None
    email_count: int
    contract_count: int
    avg_response_time_hours: float | None


class ActivityFeedItem(BaseModel):
    activity_type: str  # "email", "stage_transition", "contract_created", "sla_breach"
    entity_id: str
    entity_type: str
    title: str
    description: str
    timestamp: datetime
    actor: str | None

    model_config = ConfigDict(from_attributes=True)
