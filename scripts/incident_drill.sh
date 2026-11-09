#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${CONTRACT_ACCOUNT:?set CONTRACT_ACCOUNT}"
: "${OWNER_ACCOUNT:?set OWNER_ACCOUNT}"
API_URL="${API_URL:-http://127.0.0.1:8080}"

if [[ "${DRILL_CONFIRM:-}" != "1" ]]; then
  echo "Refusing to pause the live contract. Set DRILL_CONFIRM=1." >&2
  exit 1
fi

drill_dir="$(mktemp -d /tmp/sealquery-drill.XXXXXX)"
unpaused=0

set_paused() {
  local paused="$1"
  near contract call-function as-transaction "$CONTRACT_ACCOUNT" set_paused \
    json-args "{\"paused\":$paused}" \
    prepaid-gas '30 Tgas' attached-deposit '0 NEAR' \
    sign-as "$OWNER_ACCOUNT" network-config testnet sign-with-keychain send
}

unpause() {
  if [[ "$unpaused" -eq 0 ]]; then
    echo "== unpause"
    set_paused false
    unpaused=1
  fi
}

trap unpause EXIT

echo "== pause"
pause_output="$(set_paused true 2>&1)"
echo "$pause_output" | grep -E 'Transaction ID|Success' || true

for _ in $(seq 1 30); do
  if curl -fsS "$API_URL/api/state" | jq -e '.paused == true' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "$API_URL/api/state" | jq -e '.paused == true' >/dev/null; then
  echo "FAIL: contract did not report paused" >&2
  exit 1
fi
echo "paused=true"

echo "== query while paused"
http_code="$(
  curl -s -o "$drill_dir/query.json" -w '%{http_code}' \
    -X POST "$API_URL/api/query" \
    -H 'Content-Type: application/json' \
    -d '{"dataset_id":"retail_v1","computation_id":"spend_growth_v1"}'
)"
cat "$drill_dir/query.json"
echo
if [[ "$http_code" != "500" ]]; then
  echo "FAIL: expected HTTP 500 while paused, got $http_code" >&2
  exit 1
fi
if ! grep -q 'paused' "$drill_dir/query.json"; then
  echo "FAIL: rejection did not mention paused" >&2
  exit 1
fi

unpause

for _ in $(seq 1 30); do
  if curl -fsS "$API_URL/api/state" | jq -e '.paused == false' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "$API_URL/api/state" | jq -e '.paused == false' >/dev/null; then
  echo "FAIL: contract did not report unpaused" >&2
  exit 1
fi
echo "paused=false"
echo "DRILL PASSED"
