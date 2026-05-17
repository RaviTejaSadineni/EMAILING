from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContractResponse(BaseModel):
    id: UUID
    thread_id: UUID
    agreement_name: str | None
    agreement_type: str | None
    counterparty_name: str | None
    counterparty_email: str | None
    current_stage: str | None
    risk_score: float | None
    complexity_score: float | None
    sla_breached: bool

    model_config = ConfigDict(from_attributes=True)


class ContractClause(BaseModel):
    type: str
    evidence: str | None = None


class ContractTimeline(BaseModel):
    stage_history: list[dict]


class ContractDetail(ContractResponse):
    key_clauses: list[dict]
    delay_reasons: list[dict]
    ai_summary: str | None


class ContractStats(BaseModel):
    total_contracts: int
    by_type: dict[str, int]
    sla_breaches: int


class ContractFilter(BaseModel):
    agreement_type: str | None = None
    counterparty: str | None = None
    stage: str | None = None
