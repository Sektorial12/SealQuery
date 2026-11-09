#!/usr/bin/env python3
"""Poll SealQuery metrics and report alerts."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def fetch(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8080/api/metrics")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    while True:
        try:
            metrics = fetch(args.url, args.timeout)
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            print(f"MONITOR ERROR: {error}", file=sys.stderr)
            if args.once:
                return 1
            time.sleep(args.interval)
            continue

        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print(
                "OK"
                if metrics.get("ok")
                else "ALERT",
                f"contract={metrics.get('contract')}",
                f"queries={metrics.get('queries', {}).get('by_status', {})}",
            )
            for alert in metrics.get("alerts", []):
                print(
                    f"{alert['severity'].upper()} {alert['code']}: {alert['message']}"
                )

        if args.once:
            critical = any(
                alert.get("severity") == "critical"
                for alert in metrics.get("alerts", [])
            )
            return 2 if critical else 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
