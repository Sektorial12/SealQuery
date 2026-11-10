#!/usr/bin/env python3
"""Run the SealQuery async demo flow and print a transcript."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

TERMINAL = {"settled", "refunded", "failed", "error"}


def api(url: str, path: str, api_key: str | None = None, method: str = "GET", body: dict | None = None, idempotency: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    if idempotency:
        headers["Idempotency-Key"] = idempotency
    response = requests.request(
        method,
        f"{url.rstrip('/')}{path}",
        headers=headers,
        json=body,
        timeout=300,
    )
    payload = response.json()
    if not response.ok:
        raise RuntimeError(payload.get("detail") or payload.get("error") or response.text)
    return payload


def wait_for_job(url: str, api_key: str, job_id: str) -> dict:
    last = None
    while True:
        job = api(url, f"/api/v1/jobs/{job_id}", api_key)
        status = job["status"]
        if status != last:
            print(f"  status: {status}")
            last = status
        if status in TERMINAL:
            return job
        time.sleep(3)


def run_query(url: str, api_key: str, dataset: str, computation: str, params: dict | None, label: str) -> dict:
    key = f"demo-{uuid.uuid4()}"
    print(f"\n== {label}")
    job = api(
        url,
        "/api/v1/query",
        api_key,
        method="POST",
        body={
            "dataset_id": dataset,
            "computation_id": computation,
            **({"params": params} if params else {}),
        },
        idempotency=key,
    )
    print(f"  job: {job['job_id']} ({job['status']})")
    final = wait_for_job(url, api_key, job["job_id"])
    print(f"  query: {final.get('query_id')}")
    print(f"  proof: {final.get('proof')}")
    print(f"  request tx: https://explorer.testnet.near.org/transactions/{final.get('tx_hash')}")
    if final.get("accept_tx"):
        print(f"  accept tx: https://explorer.testnet.near.org/transactions/{final['accept_tx']}")
    if final.get("refund_tx"):
        print(f"  refund tx: https://explorer.testnet.near.org/transactions/{final['refund_tx']}")
    if final.get("owner_before") and final.get("owner_after"):
        print(f"  owner balance: {final['owner_before']} -> {final['owner_after']} yoctoNEAR")
    if final.get("error"):
        print(f"  error: {final['error']}")
    return final


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="https://sealquery-api.onrender.com")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--dataset", default="retail_v1")
    parser.add_argument("--computation", default="spend_growth_v1")
    parser.add_argument("--skip-rejected", action="store_true")
    args = parser.parse_args()

    print("SealQuery demo flow")
    print(f"api: {args.api_url}")
    health = api(args.api_url, "/api/health")
    print(f"health: {health['ok']} contract={health['contract']}")
    state = api(args.api_url, "/api/state")
    print(f"datasets: {[entry['dataset_id'] for entry in state['datasets']]}")
    print(f"paused: {state['paused']}")

    normal = run_query(args.api_url, args.api_key, args.dataset, args.computation, None, "accepted query")
    if normal.get("tx_hash"):
        attestation = api(args.api_url, f"/api/attestation/{normal['tx_hash']}")
        report = attestation.get("attestation") or {}
        print(f"  task: {report.get('task_id')} tcb={report.get('tcb_status')} proven={attestation.get('proven')}")
        bundle = Path("data/demo_proof.json")
        bundle.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(
            f"{args.api_url.rstrip('/')}/api/attestation/{normal['tx_hash']}/bundle",
            timeout=120,
        )
        response.raise_for_status()
        bundle.write_bytes(response.content)
        print(f"  bundle: {bundle} ({len(response.content)} bytes)")
        try:
            verified = subprocess.run(
                ["outlayer-verify", "bundle", str(bundle), "--offline", "--short"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            print(f"  offline verify: {verified.stdout.strip() or verified.stderr.strip()}")
        except FileNotFoundError:
            print("  offline verify: outlayer-verify not installed")

    if not args.skip_rejected:
        rejected = run_query(
            args.api_url,
            args.api_key,
            args.dataset,
            args.computation,
            {
                "period_a": "2011-11",
                "period_b": "2011-12",
                "countries": ["Canaryland"],
                "min_cohort_size": 100,
            },
            "rejected query (refund)",
        )
        print(f"  final status: {rejected['status']}")

    print("\nDemo flow complete")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"demo failed: {error}", file=sys.stderr)
        raise SystemExit(1)
