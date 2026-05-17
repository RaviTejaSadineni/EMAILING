from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database import Base


class Stakeholder(Base):
    __tablename__ = "stakeholders"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email_address: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    avg_response_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_emails: Mapped[int] = mapped_column(Integer, default=0)
    total_contracts: Mapped[int] = mapped_column(Integer, default=0)
    response_time_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    communication_patterns: Mapped[dict] = mapped_column(JSON, default=dict)
    influence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    department_mentions: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
