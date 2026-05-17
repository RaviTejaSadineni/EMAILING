from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database import Base


class EmailClassification(Base):
    __tablename__ = "email_classifications"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("emails.id", ondelete="CASCADE"), index=True)
    category: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    email_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
