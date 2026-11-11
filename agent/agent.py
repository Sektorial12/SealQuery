#!/usr/bin/env python3
"""SealQuery agent client.

Runs the complete loop on NEAR testnet:
quote -> pay -> wait -> verify attestation -> accept or refund.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import threading
import time

import requests

RPC_URL = os.environ.get("NEAR_RPC", "https://rpc.testnet.fastnear.com")
OUTLAYER_API = os.environ.get("OUTLAYER_API", "https://testnet-api.outlayer.ai")
NEAR_NETWORK = os.environ.get("NEAR_NETWORK", "testnet")
NEAR_ACCESS_KEY_FILE = os.environ.get("NEAR_ACCESS_KEY_FILE")
RPC_CONCURRENCY = max(1, int(os.environ.get("NEAR_RPC_CONCURRENCY", "3")))
_rpc_semaphore = threading.Semaphore(RPC_CONCURRENCY)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _tx_failure(tx_hash: str, signer: str) -> str:
    try:
        response = requests.post(
            RPC_URL,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "EXPERIMENTAL_tx_status",
                "params": [tx_hash, signer],
            },
            timeout=20,
        )
        payload = response.json()
        failure = payload.get("result", {}).get("status", {}).get("Failure")
        if not failure:
            return "transaction failed"
        action = failure.get("ActionError", {})
        kind = action.get("kind", {})
        detail = (
            kind.get("FunctionCallError", {}).get("ExecutionError")
            or action.get("kind", {}).get("ExecutionError")
            or json.dumps(failure)[:300]
        )
        return _ANSI_RE.sub("", str(detail))[:500]
    except Exception:
        return "transaction failed"


def _cli_detail(output: str) -> str:
    text = _ANSI_RE.sub("", output)
    text = re.sub(r"ed25519:[1-9A-HJ-NP-Za-km-z]+", "[redacted]", text)
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        lowered = line.lower()
        if any(token in lowered for token in ("error", "fail", "not found", "missing", "unable", "denied", "no such")):
            lines.append(line[:300])
    return " | ".join(lines[-3:]) if lines else "near CLI error"


def _raise_failure(tx_hash: str | None, signer: str, output: str = "") -> None:
    detail = _tx_failure(tx_hash, signer) if tx_hash else _cli_detail(output)
    raise RuntimeError(f"near transaction failed: {detail}")



def rpc_view(contract: str, method: str, args: dict) -> dict:
    encoded = base64.b64encode(json.dumps(args).encode()).decode()
    last_error: Exception | None = None
    for attempt in range(6):
        response = None
        with _rpc_semaphore:
            try:
                response = requests.post(
                    RPC_URL,
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
            except requests.RequestException as error:
                last_error = error
            if response is not None:
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    last_error = RuntimeError(
                        f"RPC {response.status_code}: {response.text[:200]}"
                    )
                else:
                    response.raise_for_status()
                    payload = response.json()
                    if "error" in payload:
                        raise RuntimeError(payload["error"])
                    data = payload["result"]["result"]
                    return json.loads(bytes(data).decode())
        time.sleep(0.5 * (2**attempt))
    raise RuntimeError(f"RPC view failed after retries: {last_error}")


def _run_transaction(command: list[str], agent: str) -> str:
    output = ""
    for attempt in range(3):
        completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
        output = completed.stdout + completed.stderr
        tx_match = re.search(r"Transaction ID:\s*([1-9A-HJ-NP-Za-km-z]+)", output)
        if completed.returncode == 0:
            return output
        if tx_match:
            _raise_failure(tx_match.group(1), agent, output)
        if "expired" in output.lower() and attempt < 2:
            time.sleep(1 + attempt)
            continue
        _raise_failure(None, agent, output)
    _raise_failure(None, agent, output)
    return output


def near_call(contract: str, method: str, args: dict, agent: str, deposit: str) -> str:
    command = [
        "near",
        "contract",
        "call-function",
        "as-transaction",
        contract,
        method,
        "json-args",
        json.dumps(args),
        "prepaid-gas",
        "200 Tgas",
        "attached-deposit",
        deposit,
        "sign-as",
        agent,
        "network-config",
        NEAR_NETWORK,
    ]
    if NEAR_ACCESS_KEY_FILE:
        command.extend(
            ["sign-with-access-key-file", NEAR_ACCESS_KEY_FILE, "send"]
        )
    else:
        command.extend(["sign-with-keychain", "send"])
    output = _run_transaction(command, agent)
    match = re.search(r"Transaction ID:\s*([1-9A-HJ-NP-Za-km-z]+)", output)
    if not match:
        raise RuntimeError("transaction id not found in near CLI output")
    return match.group(1)


def parse_query_id(output: str) -> int:
    match = re.search(r'"query_id":\s*(\d+)', output)
    if not match:
        raise RuntimeError("query id not found in transaction logs")
    return int(match.group(1))


def request_query(contract: str, agent: str, dataset: str, computation: str, params: dict) -> tuple[int, str]:
    if NEAR_ACCESS_KEY_FILE and not os.path.exists(NEAR_ACCESS_KEY_FILE):
        raise RuntimeError(f"access key file not found: {NEAR_ACCESS_KEY_FILE}")
    quote = rpc_view(contract, "quote", {"dataset_id": dataset, "computation_id": computation})
    price_yocto = int(quote["price_yocto"])
    deposit = f"{price_yocto / 1e24:.6f} NEAR"
    command = [
        "near",
        "contract",
        "call-function",
        "as-transaction",
        contract,
        "request_query",
        "json-args",
        json.dumps(
            {
                "dataset_id": dataset,
                "computation_id": computation,
                "params": json.dumps(params),
            }
        ),
        "prepaid-gas",
        "200 Tgas",
        "attached-deposit",
        deposit,
        "sign-as",
        agent,
        "network-config",
        NEAR_NETWORK,
    ]
    if NEAR_ACCESS_KEY_FILE:
        command.extend(
            ["sign-with-access-key-file", NEAR_ACCESS_KEY_FILE, "send"]
        )
    else:
        command.extend(["sign-with-keychain", "send"])
    output = _run_transaction(command, agent)
    tx_hash = re.search(r"Transaction ID:\s*([1-9A-HJ-NP-Za-km-z]+)", output)
    if not tx_hash:
        raise RuntimeError("transaction id not found in near CLI output")
    return parse_query_id(output), tx_hash.group(1)


def wait_for_result(contract: str, query_id: int, timeout_seconds: int = 90) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        query = rpc_view(contract, "get_query", {"query_id": query_id})
        if query["status"] != "pending":
            return query
        time.sleep(3)
    raise TimeoutError(f"query {query_id} did not resolve in {timeout_seconds}s")


def verify_attestation_json(
    tx_hash: str, proof_path: str | None = None
) -> tuple[bool, dict | str]:
    command = [
        "outlayer-verify",
        "tx",
        tx_hash,
        "--network",
        NEAR_NETWORK,
        "--api",
        OUTLAYER_API,
        "--json",
    ]
    if proof_path:
        command.extend(["--bundle", proof_path])
    completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
    output = completed.stdout.strip()
    try:
        report = json.loads(output)
    except json.JSONDecodeError:
        return False, (completed.stdout + completed.stderr).strip()
    checks = ["authenticity", "identity", "binding", "input", "output"]
    proven = completed.returncode == 0 and all(
        report.get(check, {}).get("verdict") == "pass" for check in checks
    )
    return proven, report


def verify_attestation(tx_hash: str, proof_path: str | None) -> tuple[bool, str]:
    command = [
        "outlayer-verify",
        "tx",
        tx_hash,
        "--network",
        NEAR_NETWORK,
        "--api",
        OUTLAYER_API,
        "--short",
    ]
    if proof_path:
        command.extend(["--bundle", proof_path])
    completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode == 0 and "PROVEN" in output, output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--dataset", default="retail_v1")
    parser.add_argument("--computation", default="spend_growth_v1")
    parser.add_argument("--params-file", required=True)
    parser.add_argument("--proof", default=None)
    args = parser.parse_args()

    params = json.loads(open(args.params_file, "r", encoding="utf-8").read())

    query_id, tx_hash = request_query(
        args.contract,
        args.agent,
        args.dataset,
        args.computation,
        params,
    )
    print(f"query_id={query_id} tx={tx_hash}")
    query = wait_for_result(args.contract, query_id)
    print(f"status={query['status']}")
    print(f"result={query.get('result')}")

    if query["status"] == "ready":
        proven, proof_output = verify_attestation(tx_hash, args.proof)
        print(proof_output)
        if proven:
            near_call(
                args.contract,
                "accept_result",
                {"query_id": query_id},
                args.agent,
                "0 NEAR",
            )
            print("settled")
            return 0
        print("attestation failed; refusing to accept")
        return 1

    if query["status"] == "failed":
        near_call(
            args.contract,
            "refund_query",
            {"query_id": query_id},
            args.agent,
            "0 NEAR",
        )
        print("refunded")
        return 2

    print(f"unexpected status: {query['status']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
