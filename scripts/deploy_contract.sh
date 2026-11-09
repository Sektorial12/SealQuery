#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${CONTRACT_ACCOUNT:?set CONTRACT_ACCOUNT}"
: "${OWNER_ACCOUNT:?set OWNER_ACCOUNT}"

NETWORK="${NEAR_NETWORK:-testnet}"
INIT="${INIT:-0}"

(
  cd contracts/sealquery
  cargo near build non-reproducible-wasm --locked --no-abi
)

WASM="target/near/sealquery/sealquery.wasm"

if [[ "$INIT" == "1" ]]; then
  near contract deploy "$CONTRACT_ACCOUNT" \
    use-file "$WASM" \
    with-init-call new \
    json-args "{\"owner\":\"$OWNER_ACCOUNT\"}" \
    prepaid-gas '100 Tgas' attached-deposit '0 NEAR' \
    network-config "$NETWORK" sign-with-keychain send
else
  near contract deploy "$CONTRACT_ACCOUNT" \
    use-file "$WASM" \
    without-init-call \
    network-config "$NETWORK" sign-with-keychain send
fi
