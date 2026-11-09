#!/usr/bin/env python3
"""SealQuery demo API and static frontend server."""

from __future__ import annotations

import hmac
import json
import os
import pathlib
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request, send_file, send_from_directory

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent.agent as agent_client

WEB_DIR = ROOT / "web"
CONTRACT = os.environ["CONTRACT_ACCOUNT"]
AGENT = os.environ["AGENT_ACCOUNT"]
API_KEY = os.environ.get("SEALQUERY_API_KEY")
RATE_LIMIT = int(os.environ.get("SEALQUERY_RATE_LIMIT_PER_MINUTE", "5"))
IDEMPOTENCY_TTL = int(os.environ.get("SEALQUERY_IDEMPOTENCY_TTL_SECONDS", "86400"))
STATE_TTL = float(os.environ.get("SEALQUERY_STATE_TTL_SECONDS", "5"))
DATASETS = json.loads(
    os.environ.get(
        "DEMO_DATASETS",
        '[["retail_v1","spend_growth_v1"],["retail_alt","spend_growth_alt"]]',
    )
)
DEFAULT_PARAMS = {
    "period_a": "2011-11",
    "period_b": "2011-12",
    "countries": ["United Kingdom"],
    "min_cohort_size": 100,
}

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")

_rate_lock = threading.Lock()
_rate_events: dict[str, list[float]] = {}
_idempotency_lock = threading.Lock()
_idempotency: dict[str, tuple[float, dict]] = {}
_query_tx_lock = threading.Lock()
QUERY_TX_PATH = ROOT / "data" / "query_tx.json"


def load_query_tx() -> dict[int, dict]:
    try:
        raw = json.loads(QUERY_TX_PATH.read_text(encoding="utf-8"))
        return {int(key): value for key, value in raw.items()}
    except Exception:
        return {}


_query_tx: dict[int, dict] = load_query_tx()
_snapshot_lock = threading.Lock()
_cache_lock = threading.Lock()
_snapshot_cache: tuple[float, dict | None] = (0.0, None)


def invalidate_snapshot() -> None:
    global _snapshot_cache
    with _cache_lock:
        _snapshot_cache = (0.0, None)


def save_query_tx() -> None:
    with _query_tx_lock:
        payload = {str(key): value for key, value in _query_tx.items()}
    QUERY_TX_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUERY_TX_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
        (
            "quote",
            {"dataset_id": dataset_id, "computation_id": computation_id},
        ),
        ("get_budget", {"agent": AGENT, "dataset_id": dataset_id}),
    ]
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = [
            pool.submit(agent_client.rpc_view, CONTRACT, method, args)
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


def check_rate_limit(identity: str) -> bool:
    now = time.time()
    with _rate_lock:
        events = [event for event in _rate_events.get(identity, []) if now - event < 60]
        if len(events) >= RATE_LIMIT:
            _rate_events[identity] = events
            return False
        events.append(now)
        _rate_events[identity] = events
        return True


def require_machine_auth():
    if not API_KEY:
        return None
    supplied = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(supplied, API_KEY):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    return None


def execute_query(body: dict) -> dict:
    dataset_id = body.get("dataset_id", DATASETS[0][0])
    computation_id = body.get("computation_id", DATASETS[0][1])
    params = body.get("params") or DEFAULT_PARAMS
    dataset = agent_client.rpc_view(
        CONTRACT, "get_dataset", {"dataset_id": dataset_id}
    )
    owner = dataset["owner"]
    owner_before = account_balance(owner)
    query_id, tx_hash = agent_client.request_query(
        CONTRACT, AGENT, dataset_id, computation_id, params
    )
    query = agent_client.wait_for_result(CONTRACT, query_id)
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
                CONTRACT,
                "accept_result",
                {"query_id": query_id},
                AGENT,
                "0 NEAR",
            )
    elif query["status"] == "failed":
        refund_tx = agent_client.near_call(
            CONTRACT,
            "refund_query",
            {"query_id": query_id},
            AGENT,
            "0 NEAR",
        )

    with _query_tx_lock:
        _query_tx[query_id] = {
            "tx_hash": tx_hash,
            "accept_tx": accept_tx,
            "refund_tx": refund_tx,
        }
    save_query_tx()
    invalidate_snapshot()

    return {
        "ok": True,
        "dataset_id": dataset_id,
        "computation_id": computation_id,
        "query_id": query_id,
        "tx_hash": tx_hash,
        "status": query["status"],
        "result": result,
        "proof": proof,
        "proof_output": proof_output,
        "accept_tx": accept_tx,
        "refund_tx": refund_tx,
        "owner": owner,
        "owner_before": owner_before,
        "owner_after": account_balance(owner),
    }


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/api/health")
def health():
    return jsonify(
        {
            "ok": True,
            "contract": CONTRACT,
            "agent": AGENT,
            "machine_auth": bool(API_KEY),
        }
    )


def snapshot() -> dict:
    global _snapshot_cache
    now = time.time()
    with _cache_lock:
        cached_at, cached = _snapshot_cache
        if cached is not None and now - cached_at < STATE_TTL:
            return cached
    with _snapshot_lock:
        now = time.time()
        with _cache_lock:
            cached_at, cached = _snapshot_cache
            if cached is not None and now - cached_at < STATE_TTL:
                return cached
        result = _build_snapshot()
        with _cache_lock:
            _snapshot_cache = (time.time(), result)
        return result


def _build_snapshot() -> dict:
    with ThreadPoolExecutor(max_workers=16) as pool:
        paused_future = pool.submit(
            agent_client.rpc_view, CONTRACT, "get_paused", {}
        )
        protocol_fee_future = pool.submit(
            agent_client.rpc_view, CONTRACT, "get_protocol_fee_bps", {}
        )
        query_ids_future = pool.submit(
            agent_client.rpc_view,
            CONTRACT,
            "get_queries_for_agent",
            {"agent": AGENT},
        )
        dataset_futures = [
            (
                dataset_id,
                computation_id,
                pool.submit(dataset_state, dataset_id, computation_id),
            )
            for dataset_id, computation_id in DATASETS
        ]
        paused = paused_future.result()
        protocol_fee_bps = protocol_fee_future.result()
        query_ids = query_ids_future.result()
        recent_futures = [
            (
                query_id,
                pool.submit(
                    agent_client.rpc_view,
                    CONTRACT,
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
        with _query_tx_lock:
            tx_by_query = dict(_query_tx)
        for query_id, future in recent_futures:
            recent.append(
                {
                    "query_id": query_id,
                    **future.result(),
                    **tx_by_query.get(query_id, {}),
                }
            )
    return {
        "contract": CONTRACT,
        "agent": AGENT,
        "paused": paused,
        "protocol_fee_bps": protocol_fee_bps,
        "datasets": datasets,
        "recent_queries": recent,
    }


@app.get("/api/state")
def state():
    return jsonify(snapshot())


@app.get("/api/metrics")
def metrics():
    snap = snapshot()
    recent = snap["recent_queries"]
    statuses = Counter(query.get("status", "unknown") for query in recent)
    agent_balance = account_balance(AGENT)
    contract_balance = account_balance(CONTRACT)
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

    low_agent = 100_000_000_000_000_000_000_000
    low_contract = 500_000_000_000_000_000_000_000
    if agent_balance is not None and int(agent_balance) < low_agent:
        alerts.append(
            {
                "severity": "critical",
                "code": "low_agent_balance",
                "message": f"Agent balance below 0.1 NEAR: {agent_balance} yoctoNEAR.",
            }
        )
    if contract_balance is not None and int(contract_balance) < low_contract:
        alerts.append(
            {
                "severity": "warning",
                "code": "low_contract_balance",
                "message": f"Contract balance below 0.5 NEAR: {contract_balance} yoctoNEAR.",
            }
        )

    total = len(recent)
    successes = statuses.get("settled", 0) + statuses.get("ready", 0)
    return jsonify(
        {
            "ok": not any(alert["severity"] == "critical" for alert in alerts),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "contract": CONTRACT,
            "agent": AGENT,
            "paused": snap["paused"],
            "protocol_fee_bps": snap["protocol_fee_bps"],
            "queries": {
                "recent": total,
                "by_status": dict(statuses),
                "recent_success_rate": round(successes / total, 4) if total else None,
            },
            "datasets": datasets,
            "balances": {
                "agent": agent_balance,
                "contract": contract_balance,
            },
            "alerts": alerts,
        }
    )


@app.get("/api/usage")
def usage():
    query_ids = agent_client.rpc_view(
        CONTRACT, "get_queries_for_agent", {"agent": AGENT}
    )
    queries = [
        agent_client.rpc_view(CONTRACT, "get_query", {"query_id": query_id})
        for query_id in query_ids
    ]
    return jsonify({"agent": AGENT, "count": len(queries), "queries": queries})


@app.post("/api/query")
def run_query():
    identity = f"browser:{request.remote_addr}"
    if not check_rate_limit(identity):
        return jsonify({"ok": False, "error": "rate limit exceeded"}), 429
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(execute_query(body))
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/v1/query")
def run_machine_query():
    auth_error = require_machine_auth()
    if auth_error:
        return auth_error
    identity = request.headers.get("X-API-Key") or request.remote_addr or "anonymous"
    if not check_rate_limit(identity):
        return jsonify({"ok": False, "error": "rate limit exceeded"}), 429

    idempotency_key = request.headers.get("Idempotency-Key")
    now = time.time()
    if idempotency_key:
        with _idempotency_lock:
            cached = _idempotency.get(idempotency_key)
            if cached and now - cached[0] < IDEMPOTENCY_TTL:
                response = jsonify(cached[1])
                response.headers["X-Idempotent-Replay"] = "true"
                return response

    body = request.get_json(silent=True) or {}
    try:
        result = execute_query(body)
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500

    if idempotency_key and result.get("ok"):
        with _idempotency_lock:
            _idempotency[idempotency_key] = (now, result)
    return jsonify(result)


@app.get("/api/v1/query/<int:query_id>")
def machine_query(query_id: int):
    auth_error = require_machine_auth()
    if auth_error:
        return auth_error
    try:
        return jsonify(
            agent_client.rpc_view(
                CONTRACT, "get_query", {"query_id": query_id}
            )
        )
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 404


@app.get("/api/proof/<tx_hash>")
def proof(tx_hash: str):
    proven, output = agent_client.verify_attestation(tx_hash, None)
    return jsonify({"proven": proven, "output": output})


@app.get("/api/attestation/<tx_hash>")
def attestation(tx_hash: str):
    proven, report = agent_client.verify_attestation_json(tx_hash, None)
    if isinstance(report, dict):
        return jsonify({"proven": proven, "attestation": report})
    return jsonify({"proven": proven, "output": report})


@app.get("/api/attestation/<tx_hash>/bundle")
def attestation_bundle(tx_hash: str):
    proof_dir = ROOT / "data" / "proofs"
    proof_dir.mkdir(parents=True, exist_ok=True)
    proof_path = proof_dir / f"{tx_hash}.json"
    proven, report = agent_client.verify_attestation_json(
        tx_hash, str(proof_path)
    )
    if not proven or not proof_path.exists():
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "attestation did not produce a proof bundle",
                    "report": report,
                }
            ),
            502,
        )
    return send_file(
        proof_path,
        mimetype="application/json",
        as_attachment=True,
        download_name=f"sealquery-{tx_hash}.json",
    )


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8080")),
        debug=False,
    )
