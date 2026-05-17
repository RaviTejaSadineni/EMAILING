from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database import Base


class EmailThread(Base):
    __tablename__ = "email_threads"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    thread_subject: Mapped[str] = mapped_column(String(1000), index=True)
    merged_subject: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    participant_emails: Mapped[list[str]] = mapped_column(JSON, default=list)
    email_count: Mapped[int] = mapped_column(Integer, default=0)
    first_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
