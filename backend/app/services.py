from __future__ import annotations

import json
import os
import sys
import threading
import time
import uuid
from datetime import timedelta
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import get_settings
from .models import (
    DatasetRecord,
    EventRecord,
    IndexerCheckpoint,
    JobRecord,
    QueryRecord,
    ServiceHeartbeat,
    utcnow,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
settings = get_settings()

os.environ.setdefault("NEAR_RPC", settings.near_rpc)
os.environ.setdefault("NEAR_NETWORK", settings.near_network)
os.environ.setdefault("OUTLAYER_API", settings.outlayer_api)

from agent import agent as agent_client  # noqa: E402

DEFAULT_PARAMS = {
    "period_a": "2011-11",
    "period_b": "2011-12",
    "countries": ["United Kingdom"],
    "min_cohort_size": 100,
}

_snapshot_lock = threading.Lock()
_cache_lock = threading.Lock()
_snapshot_cache: tuple[float, dict | None] = (0.0, None)


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def invalidate_snapshot() -> None:
    global _snapshot_cache
    with _cache_lock:
        _snapshot_cache = (0.0, None)


def account_balance(account_id: str) -> str | None:
    import requests

    for attempt in range(3):
        try:
            response = requests.post(
                agent_client.RPC_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "query",
                    "params": {
                        "request_type": "view_account",
                        "finality": "final",
                        "account_id": account_id,
                    },
                },
                timeout=15,
            )
            if response.status_code == 429 or 500 <= response.status_code < 600:
                time.sleep(0.5 * (2**attempt))
                continue
            response.raise_for_status()
            return response.json()["result"]["amount"]
        except Exception:
            time.sleep(0.5 * (2**attempt))
    return None


def dataset_state(dataset_id: str, computation_id: str) -> dict:
    calls = [
        ("get_dataset", {"dataset_id": dataset_id}),
        ("get_computation", {"computation_id": computation_id}),
        ("quote", {"dataset_id": dataset_id, "computation_id": computation_id}),
        ("get_budget", {"agent": settings.agent_account, "dataset_id": dataset_id}),
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(agent_client.rpc_view, settings.contract_account, method, args)
            for method, args in calls
        ]
        dataset, computation, quote, budget = [future.result() for future in futures]
    today = int(time.time() // 86_400)
    if int(budget.get("day", 0)) != today:
        budget = {"day": today, "count": 0}
    limit = int(dataset.get("budget_per_day", 0))
    return {
        "dataset_id": dataset_id,
        "computation_id": computation_id,
        "dataset": dataset,
        "computation": computation,
        "quote": quote,
        "budget": budget,
        "budget_limit": limit,
        "budget_exhausted": limit > 0 and int(budget.get("count", 0)) >= limit,
    }


def _tx_map(db: Session, query_ids: list[int]) -> dict[int, dict]:
    if not query_ids:
        return {}
    rows = db.query(QueryRecord).filter(QueryRecord.query_id.in_(query_ids)).all()
    result: dict[int, dict] = {}
    for row in rows:
        result[row.query_id] = {
            "tx_hash": row.tx_hash,
            "accept_tx": row.accept_tx,
            "refund_tx": row.refund_tx,
        }
    return result


def _build_snapshot(db: Session) -> dict:
    with ThreadPoolExecutor(max_workers=16) as pool:
        paused_future = pool.submit(
            agent_client.rpc_view, settings.contract_account, "get_paused", {}
        )
        protocol_fee_future = pool.submit(
            agent_client.rpc_view,
            settings.contract_account,
            "get_protocol_fee_bps",
            {},
        )
        query_ids_future = pool.submit(
            agent_client.rpc_view,
            settings.contract_account,
            "get_queries_for_agent",
            {"agent": settings.agent_account},
        )
        dataset_futures = [
            (
                dataset_id,
                computation_id,
                pool.submit(dataset_state, dataset_id, computation_id),
            )
            for dataset_id, computation_id in settings.datasets
        ]
        paused = paused_future.result()
        protocol_fee_bps = protocol_fee_future.result()
        query_ids = query_ids_future.result()
        recent_futures = [
            (
                query_id,
                pool.submit(
                    agent_client.rpc_view,
                    settings.contract_account,
                    "get_query",
                    {"query_id": query_id},
                ),
            )
            for query_id in query_ids[-5:]
        ]
        datasets = []
        for dataset_id, computation_id, future in dataset_futures:
            try:
                datasets.append(future.result())
            except Exception as error:
                if "dataset not found" in str(error):
                    continue
                datasets.append(
                    {
                        "dataset_id": dataset_id,
                        "computation_id": computation_id,
                        "error": str(error),
                    }
                )
        recent = []
        tx_by_query = _tx_map(db, [query_id for query_id, _ in recent_futures])
        for query_id, future in recent_futures:
            recent.append(
                {
                    "query_id": query_id,
                    **future.result(),
                    **tx_by_query.get(query_id, {}),
                }
            )
    return {
        "contract": settings.contract_account,
        "agent": settings.agent_account,
        "paused": paused,
        "protocol_fee_bps": protocol_fee_bps,
        "datasets": datasets,
        "recent_queries": recent,
    }


def snapshot(db: Session) -> dict:
    global _snapshot_cache
    now = time.time()
    with _cache_lock:
        cached_at, cached = _snapshot_cache
        if cached is not None and now - cached_at < settings.state_ttl_seconds:
            return cached
    with _snapshot_lock:
        now = time.time()
        with _cache_lock:
            cached_at, cached = _snapshot_cache
            if cached is not None and now - cached_at < settings.state_ttl_seconds:
                return cached
        try:
            result = _build_snapshot(db)
        except Exception:
            with _cache_lock:
                cached_at, cached = _snapshot_cache
                if cached is not None:
                    return cached
            raise
        with _cache_lock:
            _snapshot_cache = (time.time(), result)
        return result


def metrics(db: Session) -> dict:
    snap = snapshot(db)
    recent = snap["recent_queries"]
    statuses = Counter(query.get("status", "unknown") for query in recent)
    agent_balance = account_balance(settings.agent_account)
    contract_balance = account_balance(settings.contract_account)
    alerts = []

    if snap["paused"]:
        alerts.append(
            {
                "severity": "critical",
                "code": "contract_paused",
                "message": "The contract is paused; new queries are rejected.",
            }
        )

    datasets = []
    for entry in snap["datasets"]:
        if "error" in entry:
            alerts.append(
                {
                    "severity": "critical",
                    "code": "dataset_unavailable",
                    "message": f"{entry['dataset_id']}: {entry['error']}",
                }
            )
            continue
        used = int(entry["budget"].get("count", 0))
        limit = int(entry["dataset"].get("budget_per_day", 0))
        exhausted = limit > 0 and used >= limit
        datasets.append(
            {
                "dataset_id": entry["dataset_id"],
                "computation_id": entry["computation_id"],
                "owner": entry["dataset"].get("owner"),
                "used": used,
                "limit": limit,
                "exhausted": exhausted,
            }
        )
        if exhausted:
            alerts.append(
                {
                    "severity": "warning",
                    "code": "budget_exhausted",
                    "message": f"{entry['dataset_id']}: daily privacy budget exhausted.",
                }
            )

    if statuses.get("failed"):
        alerts.append(
            {
                "severity": "warning",
                "code": "recent_failed_queries",
                "message": f"{statuses['failed']} recent query failure(s).",
            }
        )
    if statuses.get("refunded"):
        alerts.append(
            {
                "severity": "info",
                "code": "recent_refunds",
                "message": f"{statuses['refunded']} recent query refund(s).",
            }
        )

    if agent_balance is not None and int(agent_balance) < 300_000_000_000_000_000_000_000:
        alerts.append(
            {
                "severity": "critical",
                "code": "low_agent_balance",
                "message": f"Agent balance below 0.3 NEAR: {agent_balance} yoctoNEAR.",
            }
        )
    recent_errors = (
        db.query(JobRecord)
        .filter(
            JobRecord.status == "error",
            JobRecord.updated_at >= utcnow() - timedelta(hours=1),
        )
        .count()
    )
    if recent_errors:
        alerts.append(
            {
                "severity": "critical",
                "code": "recent_job_errors",
                "message": f"{recent_errors} job error(s) in the last hour.",
            }
        )
    if contract_balance is not None and int(contract_balance) < 500_000_000_000_000_000_000_000:
        alerts.append(
            {
                "severity": "warning",
                "code": "low_contract_balance",
                "message": f"Contract balance below 0.5 NEAR: {contract_balance} yoctoNEAR.",
            }
        )

    service_health = service_status(db)
    for name in ("worker", "indexer"):
        info = service_health.get(name)
        if info is None:
            alerts.append(
                {
                    "severity": "critical" if name == "worker" else "warning",
                    "code": f"{name}_missing",
                    "message": f"{name} has not reported a heartbeat.",
                }
            )
            continue
        if info["stale_seconds"] <= settings.heartbeat_timeout_seconds:
            continue
        alerts.append(
            {
                "severity": "critical" if name == "worker" else "warning",
                "code": f"{name}_stale",
                "message": f"{name} heartbeat is {info['stale_seconds']}s old.",
            }
        )

    total = len(recent)
    successes = statuses.get("settled", 0) + statuses.get("ready", 0)
    return {
        "ok": not any(alert["severity"] == "critical" for alert in alerts),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "contract": settings.contract_account,
        "agent": settings.agent_account,
        "paused": snap["paused"],
        "protocol_fee_bps": snap["protocol_fee_bps"],
        "queries": {
            "recent": total,
            "by_status": dict(statuses),
            "recent_success_rate": round(successes / total, 4) if total else None,
        },
        "datasets": datasets,
        "balances": {"agent": agent_balance, "contract": contract_balance},
        "services": service_health,
        "alerts": alerts,
    }


def _upsert_dataset(db: Session, dataset_id: str, computation_id: str, dataset: dict, computation: dict) -> None:
    record = db.get(DatasetRecord, dataset_id)
    if record is None:
        record = DatasetRecord(dataset_id=dataset_id, computation_id=computation_id, version=dataset.get("version", ""), owner=dataset.get("owner", ""), data_hash=dataset.get("data_hash", ""), price_yocto=str(dataset.get("price_yocto", "0")), compute_deposit_yocto=str(dataset.get("compute_deposit_yocto", "0")), reward_yocto=str(dataset.get("reward_yocto", "0")), budget_per_day=int(dataset.get("budget_per_day", 0)), operation=computation.get("operation", ""))
        db.add(record)
    else:
        record.computation_id = computation_id
        record.version = dataset.get("version", record.version)
        record.owner = dataset.get("owner", record.owner)
        record.data_hash = dataset.get("data_hash", record.data_hash)
        record.price_yocto = str(dataset.get("price_yocto", record.price_yocto))
        record.compute_deposit_yocto = str(dataset.get("compute_deposit_yocto", record.compute_deposit_yocto))
        record.reward_yocto = str(dataset.get("reward_yocto", record.reward_yocto))
        record.budget_per_day = int(dataset.get("budget_per_day", record.budget_per_day))
        record.operation = computation.get("operation", record.operation)
    record.updated_at = utcnow()


def upsert_query(db: Session, query_id: int, query: dict, tx_hash: str | None = None, accept_tx: str | None = None, refund_tx: str | None = None) -> QueryRecord:
    record = db.get(QueryRecord, query_id)
    if record is None:
        record = QueryRecord(
            query_id=query_id,
            agent=query.get("agent", settings.agent_account),
            dataset_id=query.get("dataset_id", ""),
            computation_id=query.get("computation_id", ""),
            status=query.get("status", "unknown"),
            result=query.get("result"),
            deposit_yocto=str(query.get("deposit_yocto", "0")),
            created_block=int(query.get("created_block", 0)),
        )
        db.add(record)
    else:
        record.agent = query.get("agent", record.agent)
        record.dataset_id = query.get("dataset_id", record.dataset_id)
        record.computation_id = query.get("computation_id", record.computation_id)
        record.status = query.get("status", record.status)
        record.result = query.get("result", record.result)
        record.deposit_yocto = str(query.get("deposit_yocto", record.deposit_yocto))
        record.created_block = int(query.get("created_block", record.created_block))
    if tx_hash:
        record.tx_hash = tx_hash
    if accept_tx:
        record.accept_tx = accept_tx
    if refund_tx:
        record.refund_tx = refund_tx
    record.updated_at = utcnow()
    return record


def sync_datasets(db: Session) -> int:
    count = 0
    for dataset_id, computation_id in settings.datasets:
        try:
            dataset = agent_client.rpc_view(settings.contract_account, "get_dataset", {"dataset_id": dataset_id})
            computation = agent_client.rpc_view(settings.contract_account, "get_computation", {"computation_id": computation_id})
            _upsert_dataset(db, dataset_id, computation_id, dataset, computation)
            count += 1
        except Exception:
            db.rollback()
    db.commit()
    return count


def sync_queries(db: Session) -> int:
    query_ids = agent_client.rpc_view(
        settings.contract_account,
        "get_queries_for_agent",
        {"agent": settings.agent_account},
    )
    tx_by_query = _tx_map(db, query_ids)
    count = 0
    for query_id in query_ids:
        try:
            query = agent_client.rpc_view(settings.contract_account, "get_query", {"query_id": query_id})
            tx = tx_by_query.get(query_id, {})
            upsert_query(db, query_id, query, tx.get("tx_hash"), tx.get("accept_tx"), tx.get("refund_tx"))
            count += 1
        except Exception:
            db.rollback()
    db.commit()
    return count


def query_to_dict(record: QueryRecord) -> dict:
    return {
        "query_id": record.query_id,
        "agent": record.agent,
        "dataset_id": record.dataset_id,
        "computation_id": record.computation_id,
        "status": record.status,
        "result": record.result,
        "deposit_yocto": record.deposit_yocto,
        "created_block": record.created_block,
        "tx_hash": record.tx_hash,
        "accept_tx": record.accept_tx,
        "refund_tx": record.refund_tx,
        "error": record.error,
    }


def list_queries(db: Session, limit: int = 20) -> list[dict]:
    rows = db.query(QueryRecord).order_by(QueryRecord.query_id.desc()).limit(limit).all()
    if not rows:
        try:
            sync_queries(db)
        except Exception:
            pass
        rows = db.query(QueryRecord).order_by(QueryRecord.query_id.desc()).limit(limit).all()
    return [query_to_dict(row) for row in reversed(rows)]


def get_query(db: Session, query_id: int) -> dict | None:
    record = db.get(QueryRecord, query_id)
    if record is None:
        try:
            query = agent_client.rpc_view(settings.contract_account, "get_query", {"query_id": query_id})
            tx = _tx_map(db, [query_id]).get(query_id, {})
            record = upsert_query(db, query_id, query, tx.get("tx_hash"), tx.get("accept_tx"), tx.get("refund_tx"))
            db.commit()
        except Exception:
            return None
    return query_to_dict(record)


def job_to_dict(job: JobRecord) -> dict:
    result = None
    if job.result:
        try:
            result = json.loads(job.result)
        except json.JSONDecodeError:
            result = job.result
    return {
        "ok": True,
        "job_id": job.job_id,
        "dataset_id": job.dataset_id,
        "computation_id": job.computation_id,
        "status": job.status,
        "query_id": job.query_id,
        "tx_hash": job.tx_hash,
        "accept_tx": job.accept_tx,
        "refund_tx": job.refund_tx,
        "result": result,
        "proof": job.proof,
        "proof_output": job.proof_output or "",
        "owner": job.owner,
        "owner_before": job.owner_before,
        "owner_after": job.owner_after,
        "error": job.error,
        "attempts": job.attempts,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def enqueue_job(db: Session, body: dict[str, Any]) -> dict:
    dataset_id = body.get("dataset_id", settings.datasets[0][0])
    computation_id = body.get("computation_id", settings.datasets[0][1])
    if (dataset_id, computation_id) not in settings.datasets:
        raise ValueError("dataset/computation is not in the configured demo allowlist")
    params = body.get("params") or DEFAULT_PARAMS
    job = JobRecord(
        job_id=uuid.uuid4().hex,
        agent=settings.agent_account,
        dataset_id=dataset_id,
        computation_id=computation_id,
        params=json.dumps(params),
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job_to_dict(job)


def get_job(db: Session, job_id: str) -> dict | None:
    job = db.get(JobRecord, job_id)
    return job_to_dict(job) if job else None


def claim_job(db: Session) -> str | None:
    query = db.query(JobRecord).filter(JobRecord.status == "queued")
    if db.bind is not None and db.bind.dialect.name != "sqlite":
        query = query.with_for_update(skip_locked=True)
    job = query.order_by(JobRecord.created_at.asc()).first()
    if job is None:
        return None
    job.status = "running"
    job.attempts = (job.attempts or 0) + 1
    job.updated_at = utcnow()
    db.commit()
    return job.job_id


def _job_fail(db: Session, job: JobRecord, message: str, status: str = "error") -> None:
    job.status = status
    job.error = message[:2000]
    job.updated_at = utcnow()
    db.commit()


def run_job(db: Session, job: JobRecord) -> None:
    try:
        if (job.dataset_id, job.computation_id) not in settings.datasets:
            raise ValueError("dataset/computation is not in the configured demo allowlist")
        if agent_client.rpc_view(settings.contract_account, "get_paused", {}):
            raise RuntimeError("contract is paused")
        balance = account_balance(settings.agent_account)
        if balance is not None and int(balance) < 300_000_000_000_000_000_000_000:
            raise RuntimeError("agent balance below 0.3 NEAR; fund the demo agent")
        dataset = agent_client.rpc_view(
            settings.contract_account, "get_dataset", {"dataset_id": job.dataset_id}
        )
        job.owner = dataset["owner"]
        job.owner_before = account_balance(job.owner)
        job.updated_at = utcnow()
        db.commit()

        query_id, tx_hash = agent_client.request_query(
            settings.contract_account,
            settings.agent_account,
            job.dataset_id,
            job.computation_id,
            json.loads(job.params),
        )
        job.query_id = query_id
        job.tx_hash = tx_hash
        job.updated_at = utcnow()
        db.commit()

        query = agent_client.wait_for_result(settings.contract_account, query_id)
        result = query.get("result")
        if result:
            try:
                json.loads(result)
            except json.JSONDecodeError:
                result = json.dumps(result)

        proof = False
        proof_output = ""
        accept_tx = None
        refund_tx = None
        if query["status"] == "ready":
            proof, proof_output = agent_client.verify_attestation(tx_hash, None)
            if proof:
                accept_tx = agent_client.near_call(
                    settings.contract_account,
                    "accept_result",
                    {"query_id": query_id},
                    settings.agent_account,
                    "0 NEAR",
                )
            else:
                job.status = "failed"
                job.error = "attestation did not verify"
        elif query["status"] == "failed":
            refund_tx = agent_client.near_call(
                settings.contract_account,
                "refund_query",
                {"query_id": query_id},
                settings.agent_account,
                "0 NEAR",
            )

        if accept_tx or refund_tx:
            try:
                query = agent_client.rpc_view(
                    settings.contract_account, "get_query", {"query_id": query_id}
                )
            except Exception:
                pass

        upsert_query(db, query_id, query, tx_hash, accept_tx, refund_tx)
        job.result = result
        job.proof = proof
        job.proof_output = proof_output
        job.accept_tx = accept_tx
        job.refund_tx = refund_tx
        job.owner_after = account_balance(job.owner) if job.owner else None
        if accept_tx:
            job.status = "settled"
        elif refund_tx or query.get("status") == "refunded":
            job.status = "refunded"
        elif query.get("status") == "failed":
            job.status = "failed"
        elif not proof and query.get("status") == "ready":
            job.status = "failed"
        else:
            job.status = "ready"
        job.updated_at = utcnow()
        db.commit()
        invalidate_snapshot()
    except Exception as error:
        db.rollback()
        job = db.get(JobRecord, job.job_id)
        if job is None:
            return
        if job.query_id and not job.accept_tx and not job.refund_tx:
            try:
                query = agent_client.rpc_view(
                    settings.contract_account,
                    "get_query",
                    {"query_id": job.query_id},
                )
                if query.get("status") == "failed":
                    job.refund_tx = agent_client.near_call(
                        settings.contract_account,
                        "refund_query",
                        {"query_id": job.query_id},
                        settings.agent_account,
                        "0 NEAR",
                    )
                    job.status = "refunded"
                    upsert_query(
                        db,
                        job.query_id,
                        query,
                        job.tx_hash,
                        None,
                        job.refund_tx,
                    )
            except Exception:
                pass
        if job.status not in {"refunded", "settled"}:
            job.status = "error"
        job.error = str(error)[:2000]
        job.updated_at = utcnow()
        db.commit()
        invalidate_snapshot()


def reconcile_jobs(db: Session) -> int:
    cutoff = utcnow() - timedelta(seconds=settings.job_timeout_seconds)
    stale = (
        db.query(JobRecord)
        .filter(JobRecord.status.in_(["queued", "running"]))
        .filter(JobRecord.updated_at < cutoff)
        .all()
    )
    count = 0
    for job in stale:
        if not job.query_id:
            _job_fail(db, job, "job timed out before a query was submitted")
            count += 1
            continue
        try:
            query = agent_client.rpc_view(
                settings.contract_account, "get_query", {"query_id": job.query_id}
            )
            if query.get("status") == "failed":
                job.refund_tx = agent_client.near_call(
                    settings.contract_account,
                    "refund_query",
                    {"query_id": job.query_id},
                    settings.agent_account,
                    "0 NEAR",
                )
                job.status = "refunded"
                upsert_query(
                    db, job.query_id, query, job.tx_hash, None, job.refund_tx
                )
            elif query.get("status") == "settled":
                job.status = "settled"
                upsert_query(db, job.query_id, query, job.tx_hash, None, None)
            elif query.get("status") == "refunded":
                job.status = "refunded"
                upsert_query(db, job.query_id, query, job.tx_hash, None, None)
            elif query.get("status") == "pending":
                try:
                    job.refund_tx = agent_client.near_call(
                        settings.contract_account,
                        "refund_query",
                        {"query_id": job.query_id},
                        settings.agent_account,
                        "0 NEAR",
                    )
                    job.status = "refunded"
                    upsert_query(
                        db, job.query_id, query, job.tx_hash, None, job.refund_tx
                    )
                except Exception:
                    _job_fail(db, job, "job timed out waiting for OutLayer")
            elif query.get("status") == "ready":
                proof, proof_output = agent_client.verify_attestation(
                    job.tx_hash or "", None
                )
                if proof:
                    job.accept_tx = agent_client.near_call(
                        settings.contract_account,
                        "accept_result",
                        {"query_id": job.query_id},
                        settings.agent_account,
                        "0 NEAR",
                    )
                    job.status = "settled"
                    job.proof = True
                    job.proof_output = proof_output
                    upsert_query(
                        db,
                        job.query_id,
                        query,
                        job.tx_hash,
                        job.accept_tx,
                        None,
                    )
                else:
                    _job_fail(db, job, "attestation did not verify during reconciliation")
            else:
                _job_fail(db, job, "job timed out waiting for OutLayer")
            count += 1
        except Exception as error:
            _job_fail(db, job, f"reconciliation failed: {error}")
            count += 1
    return count


def readiness(db: Session) -> dict:
    db.execute(text("SELECT 1"))
    return {"ok": True, "database": "ok"}


def list_events(db: Session, limit: int = 50) -> list[dict]:
    rows = (
        db.query(EventRecord)
        .order_by(EventRecord.block_height.desc(), EventRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "event_id": row.event_id,
            "block_height": row.block_height,
            "tx_hash": row.tx_hash,
            "receipt_id": row.receipt_id,
            "standard": row.standard,
            "version": row.version,
            "event": row.event,
            "data": json.loads(row.data) if row.data else None,
        }
        for row in rows
    ]


def _neardata_get(path: str) -> dict | None:
    base = settings.neardata_api.rstrip("/")
    params = {"apiKey": settings.neardata_api_key} if settings.neardata_api_key else None
    last_error: Exception | None = None
    for attempt in range(5):
        response = requests.get(
            f"{base}{path}", params=params, timeout=30, allow_redirects=True
        )
        if response.status_code == 404:
            return None
        if response.status_code == 429 or 500 <= response.status_code < 600:
            retry_after = response.headers.get("Retry-After")
            try:
                delay = float(retry_after) if retry_after else min(30, 2**attempt)
            except ValueError:
                delay = min(30, 2**attempt)
            last_error = RuntimeError(
                f"Neardata {response.status_code}: {response.text[:200]}"
            )
            time.sleep(delay)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"Neardata request failed after retries: {last_error}")


def _neardata_block(height: int) -> dict | None:
    return _neardata_get(f"/v0/block/{height}")


def _apply_event(
    db: Session,
    event_name: str,
    data: list,
    tx_hash: str,
    block_height: int,
) -> None:
    first = data[0] if data and isinstance(data[0], dict) else {}
    query_id = first.get("query_id")
    if query_id is None:
        return
    query_id = int(query_id)
    query = db.get(QueryRecord, query_id)

    if event_name == "query_settled" or event_name == "query_refunded":
        try:
            view = agent_client.rpc_view(
                settings.contract_account, "get_query", {"query_id": query_id}
            )
        except Exception:
            view = None
        if view:
            request_tx = query.tx_hash if query else None
            upsert_query(
                db,
                query_id,
                view,
                request_tx,
                tx_hash if event_name == "query_settled" else None,
                tx_hash if event_name == "query_refunded" else None,
            )
        elif query:
            query.status = "settled" if event_name == "query_settled" else "refunded"
            if event_name == "query_settled":
                query.accept_tx = tx_hash
            else:
                query.refund_tx = tx_hash
            query.updated_at = utcnow()
        return

    if query is None:
        query = QueryRecord(
            query_id=query_id,
            agent=first.get("agent", settings.agent_account),
            dataset_id=first.get("dataset_id", ""),
            computation_id=first.get("computation_id", ""),
            status="pending" if event_name == "query_requested" else first.get("status", "unknown"),
            result=None,
            deposit_yocto="0",
            created_block=block_height,
            tx_hash=tx_hash if event_name == "query_requested" else None,
        )
        db.add(query)
    else:
        if event_name == "query_requested":
            query.tx_hash = tx_hash
            if not query.status or query.status == "unknown":
                query.status = "pending"
        elif event_name == "query_result":
            query.status = first.get("status", query.status)
        query.updated_at = utcnow()


def sync_events(db: Session) -> int:
    """Index NEP-297 events forward from a saved Neardata checkpoint."""
    base = settings.neardata_api.rstrip("/")
    latest_payload = _neardata_get("/v0/last_block/final")
    if not latest_payload:
        return 0
    latest = int(latest_payload["block"]["header"]["height"])

    checkpoint = db.get(IndexerCheckpoint, "events")
    if checkpoint is None:
        start = settings.event_start_block if settings.event_start_block is not None else latest
        checkpoint = IndexerCheckpoint(name="events", last_block=max(0, start - 1))
        db.add(checkpoint)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            checkpoint = db.get(IndexerCheckpoint, "events")
            if checkpoint is None:
                raise

    if settings.event_start_block is not None and checkpoint.last_block < settings.event_start_block:
        checkpoint.last_block = max(0, settings.event_start_block - 1)
        checkpoint.updated_at = utcnow()
        db.commit()
    if checkpoint.last_block >= latest:
        return 0
    if latest - checkpoint.last_block > settings.event_max_lag_blocks:
        checkpoint.last_block = max(0, latest - settings.event_max_lag_blocks)
        checkpoint.updated_at = utcnow()
        db.commit()

    end = min(latest, checkpoint.last_block + settings.event_blocks_per_sync)
    processed = 0
    for height in range(checkpoint.last_block + 1, end + 1):
        try:
            block = _neardata_block(height)
        except Exception:
            break
        if block is None:
            checkpoint.last_block = height
            db.commit()
            continue
        for shard in block.get("shards", []):
            for outcome in shard.get("receipt_execution_outcomes", []):
                receipt = outcome.get("receipt") or {}
                execution = outcome.get("execution_outcome") or {}
                result = execution.get("outcome") or {}
                receiver = receipt.get("receiver_id")
                executor = result.get("executor_id")
                if settings.contract_account not in {receiver, executor}:
                    continue
                tx_hash = outcome.get("tx_hash")
                receipt_id = receipt.get("receipt_id", "")
                logs = result.get("logs") or []
                for log_index, log in enumerate(logs):
                    if not isinstance(log, str) or not log.startswith("EVENT_JSON:"):
                        continue
                    try:
                        parsed = json.loads(log[len("EVENT_JSON:") :])
                    except json.JSONDecodeError:
                        continue
                    if parsed.get("standard") != "sealquery":
                        continue
                    event_id = f"{tx_hash}:{receipt_id}:{log_index}"
                    if db.get(EventRecord, event_id):
                        continue
                    data = parsed.get("data") or []
                    db.merge(
                        EventRecord(
                            event_id=event_id,
                            block_height=height,
                            tx_hash=tx_hash or "",
                            receipt_id=receipt_id,
                            standard=parsed.get("standard", ""),
                            version=parsed.get("version", ""),
                            event=parsed.get("event", ""),
                            data=json.dumps(data),
                        )
                    )
                    _apply_event(
                        db,
                        parsed.get("event", ""),
                        data,
                        tx_hash or "",
                        height,
                    )
        checkpoint.last_block = height
        checkpoint.updated_at = utcnow()
        db.commit()
        processed += 1
        invalidate_snapshot()
    return processed


def owner_summary(db: Session) -> dict:
    if db.query(DatasetRecord).count() == 0:
        try:
            sync_datasets(db)
        except Exception:
            pass
    configured = {dataset_id for dataset_id, _ in settings.datasets}
    datasets = {
        row.dataset_id: row
        for row in db.query(DatasetRecord).all()
        if row.dataset_id in configured
    }
    queries = [
        row for row in db.query(QueryRecord).all() if row.dataset_id in configured
    ]
    by_dataset: dict[str, dict] = {}
    for query in queries:
        entry = by_dataset.setdefault(
            query.dataset_id,
            {
                "query_count": 0,
                "settled": 0,
                "refunded": 0,
                "failed": 0,
                "last_block": 0,
            },
        )
        entry["query_count"] += 1
        entry["last_block"] = max(entry["last_block"], query.created_block or 0)
        if query.status == "settled":
            entry["settled"] += 1
        elif query.status == "refunded":
            entry["refunded"] += 1
        elif query.status == "failed":
            entry["failed"] += 1

    owners: dict[str, dict] = {}
    for dataset_id, entry in by_dataset.items():
        dataset = datasets.get(dataset_id)
        owner = dataset.owner if dataset else "unknown"
        reward = int(dataset.reward_yocto) if dataset else 0
        gross = reward * entry["settled"]
        summary = owners.setdefault(
            owner,
            {
                "owner": owner,
                "datasets": [],
                "query_count": 0,
                "settled": 0,
                "refunded": 0,
                "failed": 0,
                "gross_reward_yocto": "0",
            },
        )
        summary["datasets"].append(
            {
                "dataset_id": dataset_id,
                "query_count": entry["query_count"],
                "settled": entry["settled"],
                "refunded": entry["refunded"],
                "failed": entry["failed"],
                "last_block": entry["last_block"],
                "gross_reward_yocto": str(gross),
            }
        )
        summary["query_count"] += entry["query_count"]
        summary["settled"] += entry["settled"]
        summary["refunded"] += entry["refunded"]
        summary["failed"] += entry["failed"]
        summary["gross_reward_yocto"] = str(
            int(summary["gross_reward_yocto"]) + gross
        )

    return {"owners": list(owners.values()), "datasets": len(datasets), "queries": len(queries)}


def heartbeat(db: Session, name: str, detail: str = "") -> None:
    try:
        row = db.get(ServiceHeartbeat, name)
        if row is None:
            row = ServiceHeartbeat(name=name, last_seen=utcnow(), detail=detail)
            db.add(row)
        else:
            row.detail = detail
            row.last_seen = utcnow()
        db.commit()
    except IntegrityError:
        db.rollback()
        row = db.get(ServiceHeartbeat, name)
        if row is not None:
            row.detail = detail
            row.last_seen = utcnow()
            db.commit()


def service_status(db: Session) -> dict:
    rows = db.query(ServiceHeartbeat).all()
    now = utcnow()
    result: dict[str, dict] = {}
    for row in rows:
        last_seen = row.last_seen
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=now.tzinfo)
        result[row.name] = {
            "last_seen": last_seen.isoformat(),
            "stale_seconds": max(0, int((now - last_seen).total_seconds())),
            "detail": row.detail,
        }
    return result


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def prometheus_metrics(db: Session) -> str:
    lines = [
        "# HELP sealquery_paused Whether the contract is paused.",
        "# TYPE sealquery_paused gauge",
    ]
    snap = snapshot(db)
    lines.append(f"sealquery_paused {1 if snap['paused'] else 0}")
    lines.extend(
        [
            "# HELP sealquery_protocol_fee_bps Protocol fee in basis points.",
            "# TYPE sealquery_protocol_fee_bps gauge",
            f"sealquery_protocol_fee_bps {snap['protocol_fee_bps']}",
        ]
    )

    lines.append("# HELP sealquery_dataset_budget_used Daily queries used.")
    lines.append("# TYPE sealquery_dataset_budget_used gauge")
    for entry in snap["datasets"]:
        if "error" in entry:
            continue
        dataset_id = _label(entry["dataset_id"])
        lines.append(
            f'sealquery_dataset_budget_used{{dataset_id="{dataset_id}"}} {entry["budget"].get("count", 0)}'
        )
    lines.append("# HELP sealquery_dataset_budget_limit Daily query budget.")
    lines.append("# TYPE sealquery_dataset_budget_limit gauge")
    for entry in snap["datasets"]:
        if "error" in entry:
            continue
        dataset_id = _label(entry["dataset_id"])
        lines.append(
            f'sealquery_dataset_budget_limit{{dataset_id="{dataset_id}"}} {entry["dataset"].get("budget_per_day", 0)}'
        )

    lines.append("# HELP sealquery_queries_total Query records by status.")
    lines.append("# TYPE sealquery_queries_total gauge")
    for status, count in db.query(QueryRecord.status, func.count()).group_by(QueryRecord.status).all():
        lines.append(f'sealquery_queries_total{{status="{_label(status)}"}} {count}')

    lines.append("# HELP sealquery_jobs_total Jobs by status.")
    lines.append("# TYPE sealquery_jobs_total gauge")
    for status, count in db.query(JobRecord.status, func.count()).group_by(JobRecord.status).all():
        lines.append(f'sealquery_jobs_total{{status="{_label(status)}"}} {count}')

    lines.append("# HELP sealquery_events_total Indexed events by type.")
    lines.append("# TYPE sealquery_events_total gauge")
    for event, count in db.query(EventRecord.event, func.count()).group_by(EventRecord.event).all():
        lines.append(f'sealquery_events_total{{event="{_label(event)}"}} {count}')

    checkpoint = db.get(IndexerCheckpoint, "events")
    lines.append("# HELP sealquery_event_indexer_last_block Last indexed block height.")
    lines.append("# TYPE sealquery_event_indexer_last_block gauge")
    lines.append(f"sealquery_event_indexer_last_block {checkpoint.last_block if checkpoint else 0}")

    lines.append("# HELP sealquery_service_stale_seconds Seconds since a service heartbeat.")
    lines.append("# TYPE sealquery_service_stale_seconds gauge")
    for name, info in service_status(db).items():
        lines.append(f'sealquery_service_stale_seconds{{service="{_label(name)}"}} {info["stale_seconds"]}')

    return "\n".join(lines) + "\n"
