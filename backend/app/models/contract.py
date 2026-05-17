from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    thread_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("email_threads.id", ondelete="CASCADE"), index=True)
    agreement_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    agreement_type: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    counterparty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty_email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    current_stage: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    stage_history: Mapped[list[dict]] = mapped_column(JSON, default=list)
    lifecycle_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    complexity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    key_clauses: Mapped[list[dict]] = mapped_column(JSON, default=list)
    contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delay_reasons: Mapped[list[dict]] = mapped_column(JSON, default=list)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    predicted_completion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
