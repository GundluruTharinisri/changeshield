from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow


class Replay(Base):
    __tablename__ = "replays"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    candidate_url: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="completed")
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    passed_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    results: Mapped[list["ReplayResult"]] = relationship(cascade="all, delete-orphan", order_by="ReplayResult.id")


class ReplayResult(Base):
    __tablename__ = "replay_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    replay_id: Mapped[str] = mapped_column(ForeignKey("replays.id"))
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(500))
    expected_status: Mapped[int] = mapped_column(Integer)
    actual_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
