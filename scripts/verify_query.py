#!/usr/bin/env python3
"""Verify a SealQuery result against its OutLayer attestation."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

import requests


def view(contract: str, method: str, args: dict) -> dict:
    encoded = base64.b64encode(json.dumps(args).encode()).decode()
    response = requests.post(
        "https://rpc.testnet.near.org",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "query",
            "params": {
                "request_type": "call_function",
                "finality": "final",
                "account_id": contract,
                "method_name": method,
                "args_base64": encoded,
            },
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(payload["error"])
    return json.loads(bytes(payload["result"]["result"]).decode())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--query-id", type=int, required=True)
    parser.add_argument("--tx-hash", required=True)
    parser.add_argument("--network", default="testnet")
    parser.add_argument("--api", default="https://testnet-api.outlayer.ai")
    parser.add_argument("--proof", default=None)
    args = parser.parse_args()

    query = view(args.contract, "get_query", {"query_id": args.query_id})
    print(json.dumps(query, indent=2))

    command = [
        "outlayer-verify",
        "tx",
        args.tx_hash,
        "--network",
        args.network,
        "--api",
        args.api,
        "--short",
    ]
    if args.proof:
        command.extend(["--bundle", args.proof])
    completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
    output = completed.stdout + completed.stderr
    print(output.strip())
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
