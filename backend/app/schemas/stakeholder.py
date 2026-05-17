from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StakeholderResponse(BaseModel):
    id: UUID
    email_address: str
    name: str | None
    department: str | None
    role: str | None
    is_internal: bool
    avg_response_time: float | None
    total_emails: int
    total_contracts: int

    model_config = ConfigDict(from_attributes=True)


class StakeholderDetail(StakeholderResponse):
    response_time_distribution: dict
    communication_patterns: dict
    influence_score: float | None
    department_mentions: list[str]


class StakeholderAnalytics(BaseModel):
    response_time_distribution: dict
    communication_patterns: dict
    influence_score: float | None


class StakeholderComparison(BaseModel):
    items: list[StakeholderResponse]


class DepartmentStats(BaseModel):
    department: str
    count: int
