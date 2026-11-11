from __future__ import annotations

import time

from sqlalchemy.exc import IntegrityError

from .config import get_settings
from .db import SessionLocal, init_db
from .services import heartbeat, sync_datasets, sync_events, sync_queries


def main() -> None:
    settings = get_settings()
    init_db()
    last_state_sync = 0.0
    while True:
        db = SessionLocal()
        try:
            heartbeat(db, "indexer", "syncing")
            now = time.time()
            datasets = 0
            queries = 0
            if now - last_state_sync >= settings.indexer_interval_seconds:
                datasets = sync_datasets(db)
                queries = sync_queries(db)
                last_state_sync = now
            events = sync_events(db)
            print(
                f"indexed datasets={datasets} queries={queries} event_blocks={events}",
                flush=True,
            )
            heartbeat(db, "indexer", f"event_blocks={events}")
        except IntegrityError as error:
            db.rollback()
            print(f"indexer integrity conflict; retrying: {error}", flush=True)
            time.sleep(2)
            continue
        except Exception as error:
            db.rollback()
            print(f"indexer error: {error}", flush=True)
            try:
                heartbeat(db, "indexer", f"error: {error}")
            except Exception:
                db.rollback()
            time.sleep(max(settings.event_indexer_interval_seconds, 60))
            continue
        finally:
            db.close()
        time.sleep(settings.event_indexer_interval_seconds)


if __name__ == "__main__":
    main()
