from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DatasetRecord(Base):
    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    computation_id: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(128))
    owner: Mapped[str] = mapped_column(String(128))
    data_hash: Mapped[str] = mapped_column(String(128))
    price_yocto: Mapped[str] = mapped_column(String(64))
    compute_deposit_yocto: Mapped[str] = mapped_column(String(64))
    reward_yocto: Mapped[str] = mapped_column(String(64))
    budget_per_day: Mapped[int] = mapped_column(Integer)
    operation: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QueryRecord(Base):
    __tablename__ = "queries"

    query_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent: Mapped[str] = mapped_column(String(128))
    dataset_id: Mapped[str] = mapped_column(String(128))
    computation_id: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="requested")
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    deposit_yocto: Mapped[str] = mapped_column(String(64))
    created_block: Mapped[int] = mapped_column(Integer)
    tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    accept_tx: Mapped[str | None] = mapped_column(String(128), nullable=True)
    refund_tx: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
