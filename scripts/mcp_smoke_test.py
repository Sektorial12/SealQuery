#!/usr/bin/env python3
"""Smoke-test the SealQuery MCP stdio server against a running demo API."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def send(process: subprocess.Popen, message: dict) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(message) + "\n")
    process.stdin.flush()


def receive(process: subprocess.Popen) -> dict:
    assert process.stdout is not None
    line = process.stdout.readline()
    if not line:
        stderr = process.stderr.read() if process.stderr else ""
        raise RuntimeError(f"MCP server closed stdout: {stderr}")
    return json.loads(line)


def call(process: subprocess.Popen, request_id: int, name: str, arguments: dict) -> dict:
    send(
        process,
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
    )
    response = receive(process)
    result = response.get("result", {})
    if result.get("isError"):
        raise RuntimeError(result.get("content"))
    return json.loads(result["content"][0]["text"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", action="store_true", help="also run a paid query")
    parser.add_argument("--query-id", type=int, help="check an existing query")
    parser.add_argument("--tx-hash", help="verify an existing request transaction")
    parser.add_argument("--dataset", default="retail_v1")
    args = parser.parse_args()

    env = os.environ.copy()
    env.setdefault("SEALQUERY_API_URL", "http://127.0.0.1:8000")
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "mcp" / "server.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        send(
            process,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "smoke-test", "version": "0.1.0"},
                },
            },
        )
        initialized = receive(process)
        assert initialized["result"]["serverInfo"]["name"] == "sealquery"

        send(process, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = receive(process)["result"]["tools"]
        names = {tool["name"] for tool in tools}
        assert {"list_datasets", "quote", "run_query", "get_query", "verify_query"} <= names

        datasets = call(process, 3, "list_datasets", {})
        assert any(
            entry.get("dataset_id") == args.dataset
            for entry in datasets.get("datasets", [])
        ), datasets

        quote = call(
            process, 4, "quote", {"dataset_id": args.dataset, "computation_id": "spend_growth_v1"}
        )
        assert quote["quote"]["price_yocto"]

        if args.query:
            query = call(process, 5, "run_query", {"dataset_id": args.dataset})
            assert query["ok"] and query["proof"], query
            args.query_id = query["query_id"]
            args.tx_hash = query["tx_hash"]

        if args.query_id:
            record = call(process, 6, "get_query", {"query_id": args.query_id})
            assert record["status"] in {"ready", "settled"}, record
        if args.tx_hash:
            verified = call(process, 7, "verify_query", {"tx_hash": args.tx_hash})
            assert verified["proven"], verified

        print(
            json.dumps(
                {
                    "ok": True,
                    "tools": sorted(names),
                    "datasets": len(datasets.get("datasets", [])),
                    "quote_price_yocto": quote["quote"]["price_yocto"],
                    "query_id": args.query_id,
                    "query_status": record["status"] if args.query_id else None,
                    "proof": verified["proven"] if args.tx_hash else None,
                    "idempotency_key": query.get("idempotency_key") if args.query else None,
                }
            )
        )
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
