from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Specification(Base):
    __tablename__ = "specifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(100))
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Comparison(Base):
    __tablename__ = "comparisons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    old_spec_id: Mapped[str] = mapped_column(ForeignKey("specifications.id"))
    new_spec_id: Mapped[str] = mapped_column(ForeignKey("specifications.id"))
    status: Mapped[str] = mapped_column(String(30), default="completed")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    findings: Mapped[list["Finding"]] = relationship(cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    comparison_id: Mapped[str] = mapped_column(ForeignKey("comparisons.id"))
    severity: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(80))
    path: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    old_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
