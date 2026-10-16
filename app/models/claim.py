import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utc_now
from app.db.base import Base
from app.models.claim_status import ClaimStatus


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    patient_name: Mapped[str] = mapped_column(String(255))
    policy_number: Mapped[str] = mapped_column(String(50), index=True)
    hospital_name: Mapped[str] = mapped_column(String(255))
    diagnosis: Mapped[str] = mapped_column(Text)
    procedure: Mapped[str] = mapped_column(String(255))
    # Amount in whole currency units.
    amount_claimed: Mapped[int] = mapped_column(Integer)
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, native_enum=False, length=20),
        default=ClaimStatus.SUBMITTED,
        index=True,
    )
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
