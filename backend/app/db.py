from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
if settings.database_url.startswith("sqlite:///"):
    path = settings.database_url.removeprefix("sqlite:///")
    if path and path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_queries_dataset_id ON queries (dataset_id)",
    "CREATE INDEX IF NOT EXISTS ix_queries_status ON queries (status)",
    "CREATE INDEX IF NOT EXISTS ix_queries_created_block ON queries (created_block)",
    "CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs (status)",
    "CREATE INDEX IF NOT EXISTS ix_jobs_created_at ON jobs (created_at)",
    "CREATE INDEX IF NOT EXISTS ix_events_block_height ON events (block_height)",
    "CREATE INDEX IF NOT EXISTS ix_events_event ON events (event)",
    "CREATE INDEX IF NOT EXISTS ix_datasets_owner ON datasets (owner)",
    "CREATE INDEX IF NOT EXISTS ix_service_heartbeats_last_seen ON service_heartbeats (last_seen)",
]


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        for statement in INDEXES:
            connection.execute(text(statement))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
