from __future__ import annotations

import hmac
import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from . import services
from .config import get_settings
from .db import SessionLocal, get_db, init_db
from .store import IdempotencyStore, RateLimiter

settings = get_settings()
rate_limiter = RateLimiter(settings.rate_limit_per_minute)
idempotency = IdempotencyStore(settings.idempotency_ttl_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.indexer_on_startup:
        db = SessionLocal()
        try:
            services.sync_datasets(db)
            services.sync_queries(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title="SealQuery API",
    version="0.5.2",
    description="Private data compute for AI agents on NEAR testnet.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_machine_auth(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.api_key:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="unauthorized")


def _identity(request: Request, x_api_key: str | None = None) -> str:
    if x_api_key:
        return f"key:{x_api_key[:8]}"
    forwarded = request.headers.get("x-forwarded-for", "") if settings.trust_proxy_headers else ""
    ip = forwarded.split(",")[-1].strip() if forwarded else ""
    if not ip:
        ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"


@app.get("/api/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    try:
        return services.readiness(db)
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "version": app.version,
        "contract": settings.contract_account,
        "agent": settings.agent_account,
        "machine_auth": bool(settings.api_key),
    }


@app.get("/api/state")
def state(db: Session = Depends(get_db)) -> dict:
    try:
        return services.snapshot(db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/api/metrics")
def metrics(db: Session = Depends(get_db)) -> dict:
    try:
        return services.metrics(db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/api/queries")
def queries(limit: int = 20, db: Session = Depends(get_db)) -> dict:
    limit = min(max(limit, 1), 100)
    items = services.list_queries(db, limit)
    return {
        "agent": settings.agent_account,
        "count": len(items),
        "queries": items,
    }


@app.get("/api/queries/{query_id}")
def query_detail(query_id: int, db: Session = Depends(get_db)) -> dict:
    query = services.get_query(db, query_id)
    if query is None:
        raise HTTPException(status_code=404, detail="query not found")
    return query


@app.get("/api/usage")
def usage(db: Session = Depends(get_db)) -> dict:
    items = services.list_queries(db, 100)
    return {"agent": settings.agent_account, "count": len(items), "queries": items}


@app.get("/metrics", include_in_schema=False)
def prometheus(db: Session = Depends(get_db)) -> Response:
    return Response(
        services.prometheus_metrics(db),
        media_type="text/plain; version=0.0.4",
    )


@app.get("/api/events")
def events(limit: int = 50, db: Session = Depends(get_db)) -> dict:
    limit = min(max(limit, 1), 200)
    items = services.list_events(db, limit)
    return {"count": len(items), "events": items}


@app.get("/api/owner/summary")
def owner_summary(db: Session = Depends(get_db)) -> dict:
    return services.owner_summary(db)


@app.post("/api/query", status_code=status.HTTP_202_ACCEPTED)
def run_query(request: Request, body: dict, db: Session = Depends(get_db)) -> dict:
    if not rate_limiter.allow(_identity(request)):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    try:
        return services.enqueue_job(db, body)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/api/v1/query", status_code=status.HTTP_202_ACCEPTED)
def run_machine_query(
    request: Request,
    body: dict,
    x_api_key: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    require_machine_auth(x_api_key)
    if not rate_limiter.allow(_identity(request, x_api_key)):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    if idempotency_key:
        cached = idempotency.get(idempotency_key)
        if cached is not None and not cached.get("_pending"):
            return JSONResponse(
                content=cached,
                status_code=200,
                headers={"X-Idempotent-Replay": "true"},
            )
        if not idempotency.claim(idempotency_key):
            raise HTTPException(status_code=409, detail="idempotent request in progress")
    try:
        result = services.enqueue_job(db, body)
    except ValueError as error:
        if idempotency_key:
            idempotency.release(idempotency_key)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        if idempotency_key:
            idempotency.release(idempotency_key)
        raise HTTPException(status_code=500, detail=str(error)) from error
    if idempotency_key and result.get("ok"):
        idempotency.set(idempotency_key, result)
    return result


@app.get("/api/jobs/{job_id}")
def job(job_id: str, db: Session = Depends(get_db)) -> dict:
    result = services.get_job(db, job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="job not found")
    return result


@app.get("/api/v1/jobs/{job_id}")
def machine_job(
    job_id: str,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    require_machine_auth(x_api_key)
    result = services.get_job(db, job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="job not found")
    return result


@app.get("/api/v1/query/{query_id}")
def machine_query(
    query_id: int,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    require_machine_auth(x_api_key)
    query = services.get_query(db, query_id)
    if query is None:
        raise HTTPException(status_code=404, detail="query not found")
    return query


@app.get("/api/proof/{tx_hash}")
def proof(tx_hash: str) -> dict:
    proven, output = services.agent_client.verify_attestation(tx_hash, None)
    return {"proven": proven, "output": output}


@app.get("/api/attestation/{tx_hash}")
def attestation(tx_hash: str) -> dict:
    proven, report = services.agent_client.verify_attestation_json(tx_hash, None)
    if isinstance(report, dict):
        return {"proven": proven, "attestation": report}
    return {"proven": proven, "output": report}


@app.get("/api/attestation/{tx_hash}/bundle")
def attestation_bundle(tx_hash: str) -> FileResponse:
    proof_dir = services._path(settings.proof_dir)
    proof_dir.mkdir(parents=True, exist_ok=True)
    proof_path = proof_dir / f"{tx_hash}.json"
    proven, report = services.agent_client.verify_attestation_json(
        tx_hash, str(proof_path)
    )
    if not proven or not proof_path.exists():
        raise HTTPException(
            status_code=502,
            detail={
                "ok": False,
                "error": "attestation did not produce a proof bundle",
                "report": report if isinstance(report, dict) else str(report),
            },
        )
    return FileResponse(
        proof_path,
        media_type="application/json",
        filename=f"sealquery-{tx_hash}.json",
    )
