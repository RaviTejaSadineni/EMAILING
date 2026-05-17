from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ThreadResponse(BaseModel):
    id: UUID
    thread_subject: str
    merged_subject: str | None
    participant_emails: list[str]
    email_count: int
    first_date: datetime | None
    last_date: datetime | None
    ai_confidence: float | None

    model_config = ConfigDict(from_attributes=True)


class ThreadListResponse(BaseModel):
    items: list[ThreadResponse]
    total: int


class ThreadDetail(ThreadResponse):
    emails: list[dict]


class ThreadStats(BaseModel):
    total_threads: int
    avg_emails_per_thread: float


class MergeProgress(BaseModel):
    job_id: UUID
    status: str
    progress: float
    total_items: int
    processed_items: int
    error_message: str | None = None
