from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SentimentPoint(BaseModel):
    date: datetime | None
    stage: str | None
    sentiment: str
    score: float
    email_id: str


class SentimentTimeline(BaseModel):
    contract_id: str
    points: list[SentimentPoint]


class SentimentByEntity(BaseModel):
    entity: str
    entity_type: str  # "stakeholder" | "stage"
    avg_sentiment_score: float
    positive_count: int
    neutral_count: int
    negative_count: int


class EscalationPattern(BaseModel):
    pattern_type: str
    description: str
    frequency: int
    avg_lead_time_hours: float
    examples: list[str]


class RiskMatrixPoint(BaseModel):
    contract_id: str
    agreement_name: str | None
    risk_score: float
    cycle_time_days: float
    current_stage: str | None


class RiskMatrix(BaseModel):
    points: list[RiskMatrixPoint]


class RiskFactor(BaseModel):
    factor: str
    weight: float
    description: str


class RiskFactors(BaseModel):
    contract_id: str
    overall_risk_score: float
    factors: list[RiskFactor]


class RiskTrendPoint(BaseModel):
    period: str
    avg_risk_score: float
    high_risk_count: int


class RiskTrend(BaseModel):
    points: list[RiskTrendPoint]


class RiskAlert(BaseModel):
    contract_id: str
    agreement_name: str | None
    risk_score: float
    reasons: list[str]
    current_stage: str | None
    detected_at: datetime


class CompletionPrediction(BaseModel):
    contract_id: str
    predicted_completion_date: datetime | None
    sla_breach_probability: float
    confidence: float
    reasoning: str


class BottleneckPrediction(BaseModel):
    contract_id: str
    predicted_bottleneck_stage: str
    probability: float
    reasoning: str


class WorkloadForecast(BaseModel):
    department: str
    period: str
    forecast_count: int
    trend: str


class WhatIfResult(BaseModel):
    contract_id: str
    scenario: str
    original_completion: datetime | None
    new_completion: datetime | None
    time_saved_days: float
    reasoning: str


class Anomaly(BaseModel):
    anomaly_type: str
    severity: str  # "low" | "medium" | "high"
    entity_id: str
    entity_type: str
    description: str
    detected_at: datetime
    recommendation: str


class AnomalyList(BaseModel):
    anomalies: list[Anomaly]
    total: int


class WeeklyInsights(BaseModel):
    week_start: datetime
    week_end: datetime
    accomplishments: list[str]
    current_risks: list[str]
    bottleneck_trends: list[str]
    recommendations: list[str]
    stakeholder_highlights: list[str]
    generated_at: datetime


class ContractInsights(BaseModel):
    contract_id: str
    insights: list[str]
    risk_flags: list[str]
    recommendations: list[str]
    generated_at: datetime


class ProcessImprovement(BaseModel):
    category: str
    suggestion: str
    estimated_impact: str
    priority: str  # "high" | "medium" | "low"
