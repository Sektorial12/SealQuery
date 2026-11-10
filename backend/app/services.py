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

from sqlalchemy.orm import Session

from .config import get_settings
from .models import DatasetRecord, JobRecord, QueryRecord, utcnow

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


def load_legacy_tx() -> dict[int, dict]:
    path = _path(settings.legacy_tx_file)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {int(key): value for key, value in raw.items()}
    except Exception:
        return {}



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
    return {
        "dataset_id": dataset_id,
        "computation_id": computation_id,
        "dataset": dataset,
        "computation": computation,
        "quote": quote,
        "budget": budget,
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
    legacy = load_legacy_tx()
    for query_id in query_ids:
        if query_id not in result and query_id in legacy:
            result[query_id] = legacy[query_id]
        elif query_id in result and not any(result[query_id].values()) and query_id in legacy:
            result[query_id] = legacy[query_id]
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
        result = _build_snapshot(db)
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

    if agent_balance is not None and int(agent_balance) < 100_000_000_000_000_000_000_000:
        alerts.append(
            {
                "severity": "critical",
                "code": "low_agent_balance",
                "message": f"Agent balance below 0.1 NEAR: {agent_balance} yoctoNEAR.",
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


def execute_query(db: Session, body: dict[str, Any]) -> dict:
    dataset_id = body.get("dataset_id", settings.datasets[0][0])
    computation_id = body.get("computation_id", settings.datasets[0][1])
    params = body.get("params") or DEFAULT_PARAMS
    dataset = agent_client.rpc_view(settings.contract_account, "get_dataset", {"dataset_id": dataset_id})
    owner = dataset["owner"]
    owner_before = account_balance(owner)
    query_id, tx_hash = agent_client.request_query(
        settings.contract_account,
        settings.agent_account,
        dataset_id,
        computation_id,
        params,
    )
    query = agent_client.wait_for_result(settings.contract_account, query_id)
    result = None
    if query.get("result"):
        try:
            result = json.loads(query["result"])
        except json.JSONDecodeError:
            result = query["result"]

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
    elif query["status"] == "failed":
        refund_tx = agent_client.near_call(
            settings.contract_account,
            "refund_query",
            {"query_id": query_id},
            settings.agent_account,
            "0 NEAR",
        )

    response_status = query["status"]
    if accept_tx or refund_tx:
        try:
            query = agent_client.rpc_view(
                settings.contract_account, "get_query", {"query_id": query_id}
            )
        except Exception:
            pass
    upsert_query(db, query_id, query, tx_hash, accept_tx, refund_tx)
    db.commit()
    invalidate_snapshot()
    return {
        "ok": True,
        "dataset_id": dataset_id,
        "computation_id": computation_id,
        "query_id": query_id,
        "tx_hash": tx_hash,
        "status": response_status,
        "result": result,
        "proof": proof,
        "proof_output": proof_output,
        "accept_tx": accept_tx,
        "refund_tx": refund_tx,
        "owner": owner,
        "owner_before": owner_before,
        "owner_after": account_balance(owner),
    }


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
