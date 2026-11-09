#!/usr/bin/env python3
"""SealQuery demo API and static frontend server."""

from __future__ import annotations

import json
import os
import pathlib
import sys

from flask import Flask, jsonify, request, send_from_directory

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent.agent as agent_client

WEB_DIR = ROOT / "web"
CONTRACT = os.environ["CONTRACT_ACCOUNT"]
AGENT = os.environ["AGENT_ACCOUNT"]
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


def account_balance(account_id: str) -> str | None:
    try:
        import requests

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
        response.raise_for_status()
        return response.json()["result"]["amount"]
    except Exception:
        return None


def dataset_state(dataset_id: str, computation_id: str) -> dict:
    dataset = agent_client.rpc_view(
        CONTRACT, "get_dataset", {"dataset_id": dataset_id}
    )
    computation = agent_client.rpc_view(
        CONTRACT, "get_computation", {"computation_id": computation_id}
    )
    quote = agent_client.rpc_view(
        CONTRACT,
        "quote",
        {"dataset_id": dataset_id, "computation_id": computation_id},
    )
    budget = agent_client.rpc_view(
        CONTRACT,
        "get_budget",
        {"agent": AGENT, "dataset_id": dataset_id},
    )
    return {
        "dataset_id": dataset_id,
        "computation_id": computation_id,
        "dataset": dataset,
        "computation": computation,
        "quote": quote,
        "budget": budget,
    }


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "contract": CONTRACT, "agent": AGENT})


@app.get("/api/state")
def state():
    paused = agent_client.rpc_view(CONTRACT, "get_paused", {})
    protocol_fee_bps = agent_client.rpc_view(CONTRACT, "get_protocol_fee_bps", {})
    query_ids = agent_client.rpc_view(
        CONTRACT, "get_queries_for_agent", {"agent": AGENT}
    )
    recent = []
    for query_id in query_ids[-5:]:
        recent.append(
            agent_client.rpc_view(CONTRACT, "get_query", {"query_id": query_id})
        )
    datasets = []
    for dataset_id, computation_id in DATASETS:
        try:
            datasets.append(dataset_state(dataset_id, computation_id))
        except Exception as error:
            datasets.append(
                {
                    "dataset_id": dataset_id,
                    "computation_id": computation_id,
                    "error": str(error),
                }
            )
    return jsonify(
        {
            "contract": CONTRACT,
            "agent": AGENT,
            "paused": paused,
            "protocol_fee_bps": protocol_fee_bps,
            "datasets": datasets,
            "recent_queries": recent,
        }
    )


@app.post("/api/query")
def run_query():
    body = request.get_json(silent=True) or {}
    dataset_id = body.get("dataset_id", DATASETS[0][0])
    computation_id = body.get("computation_id", DATASETS[0][1])
    params = body.get("params") or DEFAULT_PARAMS
    try:
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

        return jsonify(
            {
                "ok": True,
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
        )
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/proof/<tx_hash>")
def proof(tx_hash: str):
    proven, output = agent_client.verify_attestation(tx_hash, None)
    return jsonify({"proven": proven, "output": output})


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8080")),
        debug=False,
    )
