#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${OUTLAYER_PROJECT_NAME:?set OUTLAYER_PROJECT_NAME}"

NETWORK="${NEAR_NETWORK:-testnet}"

cargo build -p sealquery-workload \
  --bin sealquery-approved \
  --target wasm32-wasip2 \
  --release \
  --features wasm

WASM="target/wasm32-wasip2/release/sealquery-approved.wasm"
UPLOAD_LOG="$(mktemp)"
trap 'rm -f "$UPLOAD_LOG"' EXIT

outlayer upload "$WASM" 2>&1 | tee "$UPLOAD_LOG"
URL="$(grep 'FastFS URL:' "$UPLOAD_LOG" | sed 's/.*FastFS URL: //' | tr -d '\r')"
if [[ -z "$URL" ]]; then
  echo "failed to read FastFS URL from outlayer upload" >&2
  exit 1
fi

for _ in 1 2 3 4 5; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$URL")"
  [[ "$code" == "200" ]] && break
  sleep 2
done

outlayer deploy "$OUTLAYER_PROJECT_NAME" "$URL"
