from __future__ import annotations

import time

from .config import get_settings
from .db import SessionLocal, init_db
from .models import JobRecord
from .services import claim_job, heartbeat, reconcile_jobs, run_job


def main() -> None:
    settings = get_settings()
    init_db()
    print("worker started", flush=True)
    while True:
        db = SessionLocal()
        worked = False
        try:
            reconciled = reconcile_jobs(db)
            if reconciled:
                print(f"reconciled jobs={reconciled}", flush=True)
            job_id = claim_job(db)
            if job_id:
                job = db.get(JobRecord, job_id)
                if job is not None:
                    print(f"job {job_id} running", flush=True)
                    run_job(db, job)
                    final = db.get(JobRecord, job_id)
                    print(
                        f"job {job_id} finished status={final.status if final else 'missing'}",
                        flush=True,
                    )
                    worked = True
            heartbeat(
                db,
                "worker",
                f"queued={db.query(JobRecord).filter(JobRecord.status == 'queued').count()}",
            )
        except Exception as error:
            db.rollback()
            print(f"worker error: {error}", flush=True)
        finally:
            db.close()
        if not worked:
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
