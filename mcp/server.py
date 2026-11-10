#!/usr/bin/env python3
"""Minimal MCP stdio server for the SealQuery agent API."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid

import requests

API_URL = os.environ.get("SEALQUERY_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_KEY = os.environ.get("SEALQUERY_API_KEY", "")
PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "list_datasets",
        "description": "List datasets, approved computations, owners, prices, and remaining daily budget.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "quote",
        "description": "Get the on-chain price and privacy budget for a dataset computation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_id": {"type": "string"},
                "computation_id": {"type": "string"},
            },
            "required": ["dataset_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_query",
        "description": "Pay for, execute, attest, and settle an approved computation. Returns only the aggregate result.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_id": {"type": "string"},
                "computation_id": {"type": "string"},
                "params": {"type": "object"},
                "idempotency_key": {"type": "string"},
            },
            "required": ["dataset_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_query",
        "description": "Read a query record and its settlement status from the contract.",
        "inputSchema": {
            "type": "object",
            "properties": {"query_id": {"type": "integer"}},
            "required": ["query_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "verify_query",
        "description": "Re-run OutLayer attestation verification for a request transaction.",
        "inputSchema": {
            "type": "object",
            "properties": {"tx_hash": {"type": "string"}},
            "required": ["tx_hash"],
            "additionalProperties": False,
        },
    },
]


def log(message: str) -> None:
    print(f"sealquery-mcp: {message}", file=sys.stderr, flush=True)


def headers() -> dict[str, str]:
    result = {"Content-Type": "application/json"}
    if API_KEY:
        result["X-API-Key"] = API_KEY
    return result


def api_get(path: str) -> dict:
    response = requests.get(f"{API_URL}{path}", headers=headers(), timeout=120)
    response.raise_for_status()
    return response.json()


def api_post(path: str, body: dict, idempotency_key: str | None = None) -> dict:
    request_headers = headers()
    if idempotency_key:
        request_headers["Idempotency-Key"] = idempotency_key
    response = requests.post(
        f"{API_URL}{path}", headers=request_headers, json=body, timeout=300
    )
    response.raise_for_status()
    return response.json()


def state() -> dict:
    return api_get("/api/state")


def find_dataset(dataset_id: str) -> dict:
    for entry in state().get("datasets", []):
        if entry.get("dataset_id") == dataset_id:
            return entry
    raise ValueError(f"unknown dataset: {dataset_id}")


def tool_list_datasets(_arguments: dict) -> dict:
    snapshot = state()
    datasets = []
    for entry in snapshot.get("datasets", []):
        if "error" in entry:
            datasets.append(
                {
                    "dataset_id": entry.get("dataset_id"),
                    "error": entry["error"],
                }
            )
            continue
        dataset = entry["dataset"]
        quote = entry["quote"]
        budget = entry["budget"]
        datasets.append(
            {
                "dataset_id": entry["dataset_id"],
                "computation_id": entry["computation_id"],
                "version": dataset.get("version"),
                "owner": dataset.get("owner"),
                "price_yocto": quote.get("price_yocto"),
                "compute_deposit_yocto": quote.get("compute_deposit_yocto"),
                "reward_yocto": quote.get("reward_yocto"),
                "used_today": budget.get("count"),
                "budget_per_day": dataset.get("budget_per_day"),
                "paused": snapshot.get("paused"),
            }
        )
    return {"datasets": datasets}


def tool_quote(arguments: dict) -> dict:
    dataset_id = arguments["dataset_id"]
    entry = find_dataset(dataset_id)
    return {
        "dataset_id": dataset_id,
        "computation_id": entry.get("computation_id"),
        "quote": entry.get("quote"),
        "budget": entry.get("budget"),
    }


def tool_run_query(arguments: dict) -> dict:
    dataset_id = arguments["dataset_id"]
    entry = find_dataset(dataset_id)
    body = {
        "dataset_id": dataset_id,
        "computation_id": arguments.get("computation_id")
        or entry.get("computation_id"),
    }
    if arguments.get("params"):
        body["params"] = arguments["params"]
    idempotency_key = arguments.get("idempotency_key") or f"mcp-{uuid.uuid4()}"
    result = api_post("/api/v1/query", body, idempotency_key)
    job_id = result.get("job_id")
    terminal = {"settled", "refunded", "failed", "error"}
    while job_id and result.get("status") not in terminal:
        time.sleep(3)
        result = api_get(f"/api/v1/jobs/{job_id}")
    result["idempotency_key"] = idempotency_key
    return result


def tool_get_query(arguments: dict) -> dict:
    return api_get(f"/api/v1/query/{int(arguments['query_id'])}")


def tool_verify_query(arguments: dict) -> dict:
    return api_get(f"/api/proof/{arguments['tx_hash']}")


HANDLERS = {
    "list_datasets": tool_list_datasets,
    "quote": tool_quote,
    "run_query": tool_run_query,
    "get_query": tool_get_query,
    "verify_query": tool_verify_query,
}


def response(request_id, result=None, error=None) -> dict:
    payload = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    return payload


def handle(message: dict):
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        return response(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sealquery", "version": "0.1.0"},
            },
        )
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return response(request_id, {})
    if method == "tools/list":
        return response(request_id, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if not handler:
            return response(request_id, error={"code": -32602, "message": f"unknown tool: {name}"})
        try:
            output = handler(arguments)
            return response(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(output, indent=2),
                        }
                    ],
                    "isError": False,
                },
            )
        except Exception as error:
            log(f"{name} failed: {error}")
            return response(
                request_id,
                {
                    "content": [{"type": "text", "text": str(error)}],
                    "isError": True,
                },
            )
    return response(
        request_id, error={"code": -32601, "message": f"method not found: {method}"}
    )


def main() -> None:
    log(f"starting; api={API_URL}")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as error:
            print(json.dumps(response(None, error={"code": -32700, "message": str(error)})), flush=True)
            continue
        try:
            reply = handle(message)
        except Exception as error:
            log(f"unhandled error: {error}")
            reply = response(
                message.get("id"),
                error={"code": -32603, "message": "internal error"},
            )
        if reply is not None:
            print(json.dumps(reply), flush=True)


if __name__ == "__main__":
    main()
