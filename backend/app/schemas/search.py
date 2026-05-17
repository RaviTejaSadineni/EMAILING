from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FilterParams(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    stakeholder_id: str | None = None
    stakeholder_ids: list[str] | None = None
    department: str | None = None
    contract_type: str | None = None
    category: str | None = None
    email_type: str | None = None
    urgency: str | None = None
    sentiment: str | None = None
    stage: str | None = None
    sla_status: str | None = None  # "on_track" | "at_risk" | "breached"
    risk_level: str | None = None  # "high" | "medium" | "low"
    counterparty: str | None = None
    is_internal: bool | None = None
    search: str | None = None
    sort_by: str | None = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResultItem(BaseModel):
    entity_type: str  # "email" | "contract" | "stakeholder"
    entity_id: str
    title: str
    snippet: str
    relevance_score: float


class SearchResult(BaseModel):
    query: str
    total: int
    items: list[SearchResultItem]
    emails: list[SearchResultItem] = []
    contracts: list[SearchResultItem] = []
    stakeholders: list[SearchResultItem] = []


class SearchSuggestion(BaseModel):
    text: str
    entity_type: str
    count: int


class SavedFilterCreate(BaseModel):
    name: str
    description: str | None = None
    filter_params: dict
    is_default: bool = False


class SavedFilterResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    filter_params: dict
    is_default: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
