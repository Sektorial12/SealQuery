from __future__ import annotations

import time

from .config import get_settings
from .db import SessionLocal, init_db
from .services import sync_datasets, sync_events, sync_queries


def main() -> None:
    settings = get_settings()
    init_db()
    while True:
        db = SessionLocal()
        try:
            datasets = sync_datasets(db)
            queries = sync_queries(db)
            events = sync_events(db)
            print(
                f"indexed datasets={datasets} queries={queries} event_blocks={events}",
                flush=True,
            )
        except Exception as error:
            db.rollback()
            print(f"indexer error: {error}", flush=True)
        finally:
            db.close()
        time.sleep(settings.indexer_interval_seconds)


if __name__ == "__main__":
    main()
