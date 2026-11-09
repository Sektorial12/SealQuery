#!/usr/bin/env python3
"""Read-path load test for the SealQuery API."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def hit(url: str, timeout: float) -> float | Exception:
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            response.read()
        return (time.perf_counter() - start) * 1000
    except Exception as error:
        return error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8080/api/state")
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = [
            pool.submit(hit, args.url, args.timeout) for _ in range(args.requests)
        ]
        measurements = [result.result() for result in results]

    errors = [value for value in measurements if isinstance(value, Exception)]
    timings = sorted(value for value in measurements if isinstance(value, float))
    report = {
        "url": args.url,
        "requests": args.requests,
        "concurrency": args.concurrency,
        "errors": len(errors),
        "min_ms": round(timings[0], 1) if timings else None,
        "p50_ms": round(statistics.median(timings), 1) if timings else None,
        "p95_ms": round(timings[int(len(timings) * 0.95) - 1], 1) if timings else None,
        "max_ms": round(timings[-1], 1) if timings else None,
    }
    print(json.dumps(report))
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
