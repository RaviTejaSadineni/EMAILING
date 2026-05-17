from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClassificationResponse(BaseModel):
    id: UUID
    email_id: UUID
    category: str | None
    email_type: str | None
    urgency: str | None
    sentiment: str | None
    ai_confidence: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassificationStats(BaseModel):
    by_category: dict[str, int]
    by_type: dict[str, int]
    by_urgency: dict[str, int]


class ClassificationProgress(BaseModel):
    job_id: UUID
    status: str
    progress: float
    total_items: int
    processed_items: int
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
