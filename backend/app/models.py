from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
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


class JobRecord(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent: Mapped[str] = mapped_column(String(128))
    dataset_id: Mapped[str] = mapped_column(String(128))
    computation_id: Mapped[str] = mapped_column(String(128))
    params: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    query_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    accept_tx: Mapped[str | None] = mapped_column(String(128), nullable=True)
    refund_tx: Mapped[str | None] = mapped_column(String(128), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    proof: Mapped[bool] = mapped_column(Boolean, default=False)
    proof_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    owner_before: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_after: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EventRecord(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    block_height: Mapped[int] = mapped_column(Integer)
    tx_hash: Mapped[str] = mapped_column(String(128))
    receipt_id: Mapped[str] = mapped_column(String(128))
    standard: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(32))
    event: Mapped[str] = mapped_column(String(64))
    data: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IndexerCheckpoint(Base):
    __tablename__ = "indexer_checkpoints"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_block: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
