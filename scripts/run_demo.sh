#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${CONTRACT_ACCOUNT:?set CONTRACT_ACCOUNT}"
: "${AGENT_ACCOUNT:?set AGENT_ACCOUNT}"

export NEAR_NETWORK="${NEAR_NETWORK:-testnet}"
export NEAR_RPC="${NEAR_RPC:-https://rpc.testnet.fastnear.com}"
export OUTLAYER_API="${OUTLAYER_API:-https://testnet-api.outlayer.ai}"

python3 api/server.py
